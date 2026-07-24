'use client';

import { Card, Table, TableHeader, TableRow, TableCell, TableBody } from '@tremor/react';
import type { HistoryItem } from '@/types/api';

interface HistoryTableProps {
  data: HistoryItem[];
}

export default function HistoryTable({ data }: HistoryTableProps) {
  return (
    <Card>
      <Table>
        <TableHeader>
          <TableRow>
            <TableCell className="font-medium">Timestamp</TableCell>
            <TableCell className="font-medium">Question</TableCell>
            <TableCell className="font-medium">Response</TableCell>
            <TableCell className="font-medium">Status</TableCell>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((item) => (
            <TableRow key={item.id}>
              <TableCell>
                {new Date(item.timestamp).toLocaleString()}
              </TableCell>
              <TableCell className="max-w-[300px] truncate">{item.userQuestion}</TableCell>
              <TableCell className="max-w-[400px] truncate">{item.aiResponse}</TableCell>
              <TableCell>
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    item.status === 'success'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-red-100 text-red-800'
                  }`}
                >
                  {item.status === 'success' ? 'Success' : 'Error'}
                </span>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  );
}
