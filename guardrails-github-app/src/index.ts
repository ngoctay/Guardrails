import { Probot } from "probot";

export default (app: Probot) => {
  app.on("pull_request", async (context) => {
    const pullRequest = context.payload.pull_request;
    const changedFiles = await context.octokit.pulls.listFiles({
      owner: pullRequest.base.repo.owner.login,
      repo: pullRequest.base.repo.name,
      pull_number: pullRequest.number,
    });

    const fileNames = changedFiles.data.map((file) => file.filename);
    const commentBody = `The following files were changed in this pull request:\n${fileNames.join(
      "\n"
    )}`;

    const issueComment = context.issue({
      body: commentBody,
    });
    await context.octokit.issues.createComment(issueComment);
  });
  // For more information on building apps:
  // https://probot.github.io/docs/

  // To get your app running against GitHub, see:
  // https://probot.github.io/docs/development/
};
