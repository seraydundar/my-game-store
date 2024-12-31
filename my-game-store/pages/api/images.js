// pages/api/images.js

import fs from 'fs';
import path from 'path';

export default function handler(req, res) {
  try {
    const imagesDir = path.join(process.cwd(), 'public', 'gorseller');
    const files = fs.readdirSync(imagesDir);
    const imageFiles = files.filter(file => /\.(jpg|jpeg|png|gif|svg)$/i.test(file));
    res.status(200).json({ images: imageFiles });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'Görseller yüklenemedi' });
  }
}
