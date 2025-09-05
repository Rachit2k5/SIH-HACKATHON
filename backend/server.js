const express = require('express');
const multer = require('multer');
const cors = require('cors');
const path = require('path');
const fs = require('fs');

const app = express();

app.use(cors());
app.use(express.json());

const uploadDir = path.join(__dirname, 'uploads');
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir);

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadDir),
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1e9);
    const ext = path.extname(file.originalname);
    cb(null, `photo-${uniqueSuffix}${ext}`);
  },
});
const upload = multer({ storage });

let reports = [];
let nextId = 1;

app.post('/api/reports', upload.single('photo'), (req, res) => {
  const { title, category, priority, location, description } = req.body;
  if (!title || !category || !priority || !location || !description) {
    return res.status(400).json({ error: 'Missing required fields' });
  }

  const photo = req.file ? `/uploads/${req.file.filename}` : null;

  const newReport = {
    id: nextId++,
    title,
    category,
    priority,
    location,
    description,
    photo,
    status: 'Submitted',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  reports.push(newReport);

  res.status(201).json(newReport);
});

app.get('/api/reports', (req, res) => {
  res.json(reports);
});

app.put('/api/reports/:id', (req, res) => {
  const id = parseInt(req.params.id, 10);
  const report = reports.find((r) => r.id === id);

  if (!report) {
    return res.status(404).json({ error: 'Report not found' });
  }

  const { status, title, category, priority, location, description } = req.body;

  if (status) report.status = status;
  if (title) report.title = title;
  if (category) report.category = category;
  if (priority) report.priority = priority;
  if (location) report.location = location;
  if (description) report.description = description;

  report.updated_at = new Date().toISOString();

  res.json(report);
});

app.use('/uploads', express.static(uploadDir));

// Export the express app as a handler for Vercel serverless
module.exports = app;
