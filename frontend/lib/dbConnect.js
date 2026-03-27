import mongoose from 'mongoose';

let cached = global.mongoose;

if (!cached) {
  cached = global.mongoose = { conn: null, promise: null };
}

function getMongoUri() {
  return process.env.MONGO_URI || process.env.MONGODB_URI || process.env.MONGO_URL || '';
}

export default async function dbConnect() {
  const mongoUri = getMongoUri();

  if (!mongoUri) {
    const error = new Error('MongoDB connection is not configured. Set MONGO_URI, MONGODB_URI, or MONGO_URL.');
    error.statusCode = 500;
    throw error;
  }

  if (cached.conn) {
    return cached.conn;
  }

  if (!cached.promise) {
    cached.promise = mongoose.connect(mongoUri, {
      bufferCommands: false,
    });
  }

  cached.conn = await cached.promise;
  return cached.conn;
}
