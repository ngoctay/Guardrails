import express, { Express, Request, Response } from 'express';
import axios from 'axios';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000';

export function createWebServer(): Express {
  const app = express();

  // Set view engine
  app.set('view engine', 'ejs');
  app.set('views', path.join(__dirname, '../views'));

  // Middleware
  app.use(express.static(path.join(__dirname, '../public')));
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));

  // Health check
  app.get('/', async (_req: Request, res: Response) => {
    try {
      const health = await axios.get(`${BACKEND_URL}/health`);
      res.render('index', {
        title: 'Guardrails Dashboard',
        backendHealthy: health.status === 200,
        backendUrl: BACKEND_URL,
      });
    } catch (error) {
      res.render('index', {
        title: 'Guardrails Dashboard',
        backendHealthy: false,
        error: 'Backend API is not reachable',
      });
    }
  });

  // Dashboard page
  app.get('/dashboard', async (req: Request, res: Response) => {
    try {
      const daysParam = req.query.days || '7';
      const days = parseInt(daysParam as string);

      const response = await axios.get(`${BACKEND_URL}/api/audit`, {
        params: { days, limit: 100 },
      });

      res.render('dashboard', {
        title: 'Audit Log Dashboard',
        events: response.data.events,
        summary: response.data.summary,
        days,
      });
    } catch (error) {
      res.status(500).render('error', {
        title: 'Error',
        error: 'Failed to fetch audit logs',
      });
    }
  });

  // Audit logs API
  app.get('/api/audit-logs', async (req: Request, res: Response) => {
    try {
      const days = req.query.days || '7';
      const repo = req.query.repo || '';
      const limit = req.query.limit || '100';

      const response = await axios.get(`${BACKEND_URL}/api/audit`, {
        params: {
          days: parseInt(days as string),
          repo: repo || undefined,
          limit: parseInt(limit as string),
        },
      });

      res.json(response.data);
    } catch (error: any) {
      res.status(500).json({
        error: 'Failed to fetch audit logs',
        message: error.message,
      });
    }
  });

  // Insights page
  app.get('/insights', async (req: Request, res: Response) => {
    try {
      const days = req.query.days || '30';
      const response = await axios.get(`${BACKEND_URL}/api/insights`, {
        params: { days: parseInt(days as string) },
      });

      res.render('insights', {
        title: 'Security Insights',
        data: response.data,
        days,
      });
    } catch (error) {
      res.status(500).render('error', {
        title: 'Error',
        error: 'Failed to fetch insights',
      });
    }
  });

  // Rules page
  app.get('/rules', async (_req: Request, res: Response) => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/rules`);

      res.render('rules', {
        title: 'Security Rules',
        rules: response.data.rules,
      });
    } catch (error) {
      res.status(500).render('error', {
        title: 'Error',
        error: 'Failed to fetch rules',
      });
    }
  });

  // Audit log detail page
  app.get('/audit/:eventId', async (req: Request, res: Response) => {
    try {
      // For now, we'll fetch all events and filter
      // In production, add a specific endpoint for single event
      const response = await axios.get(`${BACKEND_URL}/api/audit`, {
        params: { days: 90, limit: 1000 },
      });

      const event = response.data.events.find(
        (e: any) => e.event_id === req.params.eventId
      );

      if (!event) {
        return res.status(404).render('error', {
          title: 'Not Found',
          error: 'Audit event not found',
        });
      }

      res.render('audit-detail', {
        title: 'Audit Log Detail',
        event,
      });
    } catch (error) {
      res.status(500).render('error', {
        title: 'Error',
        error: 'Failed to fetch audit log details',
      });
    }
  });

  // Export audit logs
  app.post('/api/export', async (req: Request, res: Response) => {
    try {
      const format = req.body.format || 'json';

      const response = await axios.post(`${BACKEND_URL}/api/audit/export`, {
        format,
      });

      res.json(response.data);
    } catch (error: any) {
      res.status(500).json({
        error: 'Failed to export audit logs',
        message: error.message,
      });
    }
  });

  // Settings page
  app.get('/settings', (_req: Request, res: Response) => {
    res.render('settings', {
      title: 'Settings',
      backendUrl: BACKEND_URL,
    });
  });

  // Search endpoint
  app.get('/api/search', async (req: Request, res: Response) => {
    try {
      const query = req.query.q as string;
      const days = parseInt(req.query.days as string) || 30;

      const response = await axios.get(`${BACKEND_URL}/api/audit`, {
        params: { days, limit: 1000 },
      });

      // Simple client-side search
      const events = response.data.events.filter((e: any) => {
        const searchStr = query.toLowerCase();
        return (
          e.repo_name.toLowerCase().includes(searchStr) ||
          e.pr_number.toString().includes(searchStr) ||
          e.event_id.toLowerCase().includes(searchStr)
        );
      });

      res.json({
        results: events,
        total: events.length,
        query,
      });
    } catch (error: any) {
      res.status(500).json({
        error: 'Search failed',
        message: error.message,
      });
    }
  });

  // Error handler
  app.use((err: any, _req: Request, res: Response, _next: any) => {
    console.error(err);
    res.status(500).render('error', {
      title: 'Error',
      error: 'An unexpected error occurred',
    });
  });

  return app;
}

export function startWebServer(port: number = 3001) {
  const app = createWebServer();

  // Start web server on specified port (default 3001 to avoid conflict with Probot)
  const server = app.listen(port, () => {
    console.log(`[WebServer] 🌐 Dashboard running on http://localhost:${port}`);
    console.log(`[WebServer] Backend API: ${BACKEND_URL}`);
  });

  server.on('error', (err: any) => {
    if (err.code === 'EADDRINUSE') {
      console.error(`[WebServer] ❌ Port ${port} is already in use. Try setting WEB_PORT environment variable.`);
    } else {
      console.error(`[WebServer] ❌ Server error:`, err);
    }
  });

  return app;
}
