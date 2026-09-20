import {sqliteTable,text} from 'drizzle-orm/sqlite-core';
export const snapshots=sqliteTable('snapshots',{id:text('id').primaryKey(),payload:text('payload').notNull(),updatedAt:text('updated_at').notNull()});
