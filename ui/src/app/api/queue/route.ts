import { NextResponse } from 'next/server';
import prisma from '@/server/prisma';

const getErrorMessage = (error: unknown) => {
  if (error instanceof Error) return error.message;
  return `${error}`;
};

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);

  try {
    const queues = await prisma.queue.findMany({
      orderBy: { gpu_ids: 'asc' },
    });
    return NextResponse.json({ queues: queues });
  } catch (error) {
    console.error(error);
    return NextResponse.json({ error: 'Failed to fetch queue', details: getErrorMessage(error) }, { status: 500 });
  }
}
