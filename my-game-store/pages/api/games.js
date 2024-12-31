import sqlite3 from 'sqlite3';
import { open } from 'sqlite';

export default async function handler(req, res) {
  const db = await open({
    filename: './game_data.db', // Veritabanı dosyası
    driver: sqlite3.Database,
  });

  const games = await db.all('SELECT oyun_adi AS "Game Name", steam_fiyati AS "Steam Price", epic_fiyati AS "Epic Price", metascore AS "Metascore", steam_url AS "Steam URL", epic_url AS "Epic URL" FROM games');
  await db.close();

  res.status(200).json(games); // Veriyi JSON olarak döndür
}
