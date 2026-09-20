import {env} from 'cloudflare:workers';
export async function database(){
 const db=(env as unknown as {DB:D1Database}).DB;
 if(!db) throw new Error('Cloud database unavailable');
 await db.prepare('CREATE TABLE IF NOT EXISTS snapshots (id TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT NOT NULL)').run();
 return db;
}
