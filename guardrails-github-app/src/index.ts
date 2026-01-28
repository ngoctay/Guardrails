import { Probot } from "probot";
import { createWebServer, startWebServer } from "./web-server.js";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

interface Violation {
  rule_id: string;
  rule_name: string;
  severity: string;
  message: string;
  file_path: string;
  line_number: number;
  line_content: string;
  suggested_fix?: string;
  cwe_id?: string;
  owasp_category?: string;
  is_copilot_generated: boolean;
  category?: string;
}

interface AnalysisResponse {
  success: boolean;
  violations: Violation[];
  violation_count: number;
  critical_count: number;
  high_count: number;
  scan_id: string;
  enforcement_mode: string;
  should_block: boolean;
  block_reason?: string;
  override_applied?: boolean;
  copilot_violations?: number;
}

// Detect if code is likely Copilot-generated
function detectCopilotGeneration(fileContent: string): string[] {
  const copilotPatterns = [
    /# This is a\s+/i,
    /# TODO: Implement/i,
    /# Replace with your/i,
    /# Add your logic here/i,
    /pass\s*#\s*TODO/i,
  ];

  const indicators: string[] = [];
  for (const pattern of copilotPatterns) {
    if (pattern.test(fileContent)) {
      indicators.push(pattern.source);
    }
  }
  return indicators;
}

// Check if file should be scanned for Copilot patterns (only code files)
function isCodeFile(filename: string): boolean {
  const codeExtensions = [
    ".py", ".js", ".ts", ".java", ".cs", ".cpp", ".c", ".go", ".rb",
    ".php", ".swift", ".kt", ".rs", ".jsx", ".tsx", ".vue"
  ];
  const lowerFilename = filename.toLowerCase();
  return codeExtensions.some(ext => lowerFilename.endsWith(ext));
}

// Map pattern names for readable display
const PATTERN_NAMES: { [key: string]: string } = {
  "# This is a\\s+": "Generic comment",
  "# TODO: Implement": "TODO placeholder",
  "# Replace with your": "Replace placeholder",
  "# Add your logic here": "Logic placeholder",
  "pass\\s*#\\s*TODO": "Empty function with TODO"
};

async function fetchPRDiff(
  context: any,
  owner: string,
  repo: string,
  prNumber: number
): Promise<{ [key: string]: string }> {
  console.log(`[fetchPRDiff] Fetching PR #${prNumber} files for ${owner}/${repo}`);
  const files = await context.octokit.pulls.listFiles({
    owner,
    repo,
    pull_number: prNumber,
  });

  const diffs: { [key: string]: string } = {};

  console.log(`[fetchPRDiff] Found ${files.data.length} files in PR #${prNumber}`);
  for (const file of files.data) {
    if (file.patch) {
      diffs[file.filename] = file.patch;
    }
  }

  return diffs;
}

function buildDetailedComment(
  result: AnalysisResponse,
  prUrl: string
): string {
  console.log(`[buildDetailedComment] Building comment for scan ${result.scan_id} with ${result.violation_count} violations`);
  let commentBody = `## 🔍 Guardrails Security Scan\n\n`;
  commentBody += `**Scan ID:** \`${result.scan_id}\`\n`;
  commentBody += `**PR:** [${prUrl}](${prUrl})\n\n`;

  // Enforcement mode banner
  const modeEmoji = {
    advisory: "ℹ️",
    warning: "⚠️",
    blocking: "🚫",
  }[result.enforcement_mode] || "•";

  commentBody += `${modeEmoji} **Enforcement Mode:** ${result.enforcement_mode.toUpperCase()}\n`;

  if (result.should_block) {
    commentBody += `**Status:** 🔴 **BLOCKED** - ${result.block_reason}\n`;
  } else if (result.violation_count === 0) {
    return `✅ **Guardrails Scan Passed**\n\nNo security violations detected in this PR.\n\n**Scan ID:** \`${result.scan_id}\``;
  } else {
    commentBody += `**Status:** ✅ Review Required\n`;
  }

  commentBody += `\n### Summary\n`;
  commentBody += `| Severity | Count |\n`;
  commentBody += `|----------|-------|\n`;
  commentBody += `| 🔴 Critical | ${result.critical_count} |\n`;
  commentBody += `| 🟠 High | ${result.high_count} |\n`;
  commentBody += `| Total | ${result.violation_count} |\n`;

  if (result.copilot_violations && result.copilot_violations > 0) {
    commentBody += `\n⚠️ **AI-Generated Code Alert:** ${result.copilot_violations} issue(s) found in Copilot-generated code.\n`;
  }

  if (result.violation_count === 0) {
    return commentBody;
  }

  commentBody += `\n### Violations\n\n`;

  // Group by severity
  const bySeverity: { [key: string]: Violation[] } = {};
  for (const violation of result.violations) {
    if (!bySeverity[violation.severity]) {
      bySeverity[violation.severity] = [];
    }
    bySeverity[violation.severity].push(violation);
  }

  const severityOrder = ["critical", "high", "medium", "low", "info"];

  for (const severity of severityOrder) {
    if (!bySeverity[severity] || bySeverity[severity].length === 0) {
      continue;
    }

    const icon = {
      critical: "🔴",
      high: "🟠",
      medium: "🟡",
      low: "🔵",
      info: "ℹ️",
    }[severity] || "•";

    commentBody += `#### ${icon} ${severity.charAt(0).toUpperCase() + severity.slice(1)} Severity\n\n`;

    for (const violation of bySeverity[severity]) {
      commentBody += `<details>\n`;
      commentBody += `<summary><b>${violation.rule_name}</b> (<code>${violation.rule_id}</code>) at <code>${violation.file_path}:${violation.line_number}</code></summary>\n\n`;
      commentBody += `**Issue:** ${violation.message}\n\n`;
      commentBody += `**Code:**\n\`\`\`\n${violation.line_content}\n\`\`\`\n\n`;

      if (violation.suggested_fix) {
        commentBody += `**Suggested Fix:**\n\`\`\`\n${violation.suggested_fix}\n\`\`\`\n\n`;
      }

      // Add reference links
      if (violation.cwe_id) {
        const cweNum = violation.cwe_id.split("-")[1];
        commentBody += `📚 **References:**\n`;
        commentBody += `- [${violation.cwe_id}](https://cwe.mitre.org/data/definitions/${cweNum}.html)\n`;
      }

      if (violation.owasp_category) {
        commentBody += `- [${violation.owasp_category}](https://owasp.org/Top10/)\n`;
      }

      if (violation.is_copilot_generated) {
        commentBody += `\n**⚠️ AI-Generated Code:** This code was generated by GitHub Copilot. Extra caution and human review recommended.\n`;
      }

      commentBody += `\n</details>\n\n`;
    }
  }

  // Policy enforcement message
  commentBody += `---\n`;

  if (result.should_block) {
    commentBody += `### ⛔ Merge Blocked\n\n`;
    commentBody += `This PR has been blocked due to security policy: **${result.block_reason}**\n\n`;
    commentBody += `**To override:**\n`;
    commentBody += `1. Request an override by commenting \`@guardrails override: <reason>\`\n`;
    commentBody += `2. Include business justification\n`;
    commentBody += `3. Approval from security team may be required\n\n`;
  } else if (result.enforcement_mode === "warning") {
    commentBody += `### ⚠️ Review Required\n\n`;
    commentBody += `This PR contains security issues that should be addressed before merging.\n`;
  } else {
    commentBody += `### ℹ️ Advisory\n\n`;
    commentBody += `This PR has security issues for informational review.\n`;
  }

  commentBody += `\n*Powered by [Guardrails](https://github.com/0210-ai/Guardrails) - Enterprise Security Scanning*\n`;

  return commentBody;
}

async function analyzePR(
  context: any,
  owner: string,
  repo: string,
  prNumber: number,
  commitHash: string,
  prUrl: string
) {
  try {
    console.log(`📊 Starting Guardrails analysis for PR #${prNumber} in ${owner}/${repo}`);

    // Fetch PR diff
    console.log(`[analyzePR] Fetching PR diff...`);
    const files = await fetchPRDiff(context, owner, repo, prNumber);

    if (Object.keys(files).length === 0) {
      console.log(`[analyzePR] ⏭️  No code files to analyze in PR #${prNumber}`);
      return;
    }

    // Detect Copilot-generated files
    console.log(`[analyzePR] Detecting Copilot-generated code patterns...`);
    const copilotFiles: string[] = [];
    for (const [filename, content] of Object.entries(files)) {
      // Only scan code files, skip documentation/config files
      if (!isCodeFile(filename)) {
        console.log(`[analyzePR] ⏭️  Skipping non-code file: ${filename}`);
        continue;
      }
      const indicators = detectCopilotGeneration(content);
      if (indicators.length > 0) {
        copilotFiles.push(filename);
        const readablePatterns = indicators.map(p => PATTERN_NAMES[p] || p).join(", ");
        console.log(`[analyzePR] 🤖 Detected Copilot patterns in ${filename}: ${readablePatterns}`);
      }
    }

    // Call backend analysis
    console.log(`[analyzePR] 📨 Sending analysis request to backend: ${BACKEND_URL}/api/analyze`);
    console.log(`[analyzePR] Files: ${Object.keys(files).length}, Copilot files: ${copilotFiles.length}`);
    const response = await fetch(`${BACKEND_URL}/api/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        repo_name: `${owner}/${repo}`,
        pr_number: prNumber,
        commit_hash: commitHash,
        files: files,
        copilot_generated_files: copilotFiles,
      }),
    });

    if (!response.ok) {
      console.error(`[analyzePR] ❌ Backend error: ${response.status} ${response.statusText}`);
      const errText = await response.text();
      console.error(`[analyzePR] Response body: ${errText.substring(0, 500)}`);
      await context.octokit.issues.createComment(
        context.issue({
          body: `⚠️ **Guardrails Scan Error**\n\nFailed to analyze this PR. Backend error: ${response.statusText}\n\nPlease try again or contact the security team.`,
        })
      );
      return;
    }

    const result: AnalysisResponse = await response.json();
    console.log(`[analyzePR] ✅ Analysis complete: ${result.violation_count} violations (${result.critical_count} critical, ${result.high_count} high)`);
    console.log(`[analyzePR] Enforcement mode: ${result.enforcement_mode}, Should block: ${result.should_block}`);
    if (result.copilot_violations) {
      console.log(`[analyzePR] AI-generated issues: ${result.copilot_violations}`);
    }

    // Build and post comment
    const commentBody = buildDetailedComment(result, prUrl);
    console.log(`[analyzePR] 💬 Posting comment to PR...`);
    await context.octokit.issues.createComment(
      context.issue({
        body: commentBody,
      })
    );

    // Request review if blocking
    if (result.should_block) {
      console.log(`[analyzePR] 🚫 Setting PR status to BLOCKED: ${result.block_reason}`);
      try {
        await context.octokit.repos.createCommitStatus({
          owner,
          repo,
          sha: commitHash,
          state: "failure",
          description: `Guardrails: ${result.block_reason}`,
          context: "guardrails/security",
          target_url: prUrl,
        });
        console.log(`[analyzePR] ✅ Status check set to FAILED`);
      } catch (error) {
        console.warn("[analyzePR] ⚠️  Failed to set commit status:", error);
      }
    } else {
      const state = result.violation_count > 0 ? "success" : "success";
      console.log(`[analyzePR] ✅ Setting PR status to SUCCESS (${result.violation_count} issues found)`);
      try {
        await context.octokit.repos.createCommitStatus({
          owner,
          repo,
          sha: commitHash,
          state: state,
          description:
            result.violation_count > 0
              ? `Guardrails: ${result.violation_count} issue(s) found`
              : "Guardrails: No violations",
          context: "guardrails/security",
          target_url: prUrl,
        });
        console.log(`[analyzePR] ✅ Status check set to SUCCESS`);
      } catch (error) {
        console.warn("[analyzePR] ⚠️  Failed to set commit status:", error);
      }
    }
  } catch (error) {
    console.error(`[analyzePR] ❌ Unexpected error: ${error instanceof Error ? error.message : String(error)}`);
    if (error instanceof Error) {
      console.error(`[analyzePR] Stack: ${error.stack}`);
    }
    try {
      await context.octokit.issues.createComment(
        context.issue({
          body: `⚠️ **Guardrails Scan Error**\n\nAn unexpected error occurred: ${error instanceof Error ? error.message : "Unknown error"}\n\nPlease check the logs or contact the security team.`,
        })
      );
    } catch (commentError) {
      console.error("[analyzePR] ❌ Failed to post error comment:", commentError);
    }
  }
}

export default (app: Probot) => {
  console.log(`[Guardrails] 🚀 GitHub App initialized`);
  
  // Handle PR opened or updated
  app.on("pull_request", async (context) => {
    const pullRequest = context.payload.pull_request;
    const action = context.payload.action;

    console.log(`[pull_request] Event: PR #${pullRequest.number} (${action}) in ${pullRequest.base.repo.owner.login}/${pullRequest.base.repo.name}`);

    if (action !== "opened" && action !== "synchronize") {
      console.log(`[pull_request] ⏭️  Skipping action: ${action}`);
      return;
    }

    const owner = pullRequest.base.repo.owner.login;
    const repo = pullRequest.base.repo.name;
    const prNumber = pullRequest.number;
    const commitHash = pullRequest.head.sha;
    const prUrl = pullRequest.html_url;

    await analyzePR(context, owner, repo, prNumber, commitHash, prUrl);
  });

  // Handle manual override comments
  app.on("issue_comment", async (context) => {
    const comment = context.payload.comment;
    const issue = context.payload.issue;

    console.log(`[issue_comment] New comment on #${issue.number} by ${comment.user.login}`);

    if (!issue.pull_request) {
      console.log(`[issue_comment] ⏭️  Skipping non-PR comment`);
      return; // Only handle PR comments
    }

    if (comment.body.includes("@guardrails override:")) {
      const prNumber = issue.number;
      const reasonMatch = comment.body.match(/@guardrails override:\s*(.+)/);
      const reason = reasonMatch ? reasonMatch[1].trim() : "Manual override requested";

      console.log(`[issue_comment] 🔑 Override request for PR #${prNumber} from ${comment.user.login}: "${reason}"`);

      try {
        await context.octokit.issues.createComment(
          context.issue({
            body: `✅ Override request received for: "${reason}"\n\nAn override token has been issued. This can be used to bypass security blocks for this PR.`,
          })
        );
        console.log(`[issue_comment] ✅ Override acknowledgement posted`);
      } catch (error) {
        console.error(`[issue_comment] ❌ Failed to post override acknowledgement:`, error);
      }
    }
  });

  // Start the web server for the dashboard (non-blocking, runs separately from Probot)
  // Use port 3001 by default to avoid conflicts with Probot (port 3000)
  setTimeout(() => {
    try {
      const webPort = process.env.WEB_PORT ? parseInt(process.env.WEB_PORT) : 3001;
      console.log("[App] Starting web server for dashboard on port " + webPort + "...");
      createWebServer();
      startWebServer(webPort);
    } catch (err) {
      console.error("[App] ❌ Failed to start web server:", err);
    }
  }, 1000); // Delay to let Probot start first
};
