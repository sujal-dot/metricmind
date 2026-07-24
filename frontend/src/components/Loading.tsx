'use client';

export default function Loading({
  text = 'Loading...',
}: {
  text?: string;
}) {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="flex flex-col items-center gap-2">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-500 border-t-transparent"></div>
        <p className="text-gray-600">{text}</p>
      </div>
    </div>
  );
}
