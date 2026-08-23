import { cn } from '@/lib/utils';

interface TableProps {
  headers: string[];
  children: React.ReactNode;
  className?: string;
  stickyHeader?: boolean;
}

export function Table({ headers, children, className, stickyHeader }: TableProps) {
  return (
    <div className={cn('w-full overflow-auto scrollbar-thin', className)}>
      <table className="w-full caption-bottom text-sm">
        <thead className={cn('border-b bg-muted/30', stickyHeader && 'sticky top-0 z-10')}>
          <tr>
            {headers.map((header, i) => (
              <th key={i} className="h-10 px-4 text-left text-xs font-medium uppercase tracking-wide text-muted-foreground">
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">{children}</tbody>
      </table>
    </div>
  );
}

export function TableRow({ children, className, ...props }: React.HTMLAttributes<HTMLTableRowElement>) {
  return (
    <tr className={cn('transition-colors hover:bg-muted/40', className)} {...props}>
      {children}
    </tr>
  );
}

export function TableCell({ children, className, ...props }: React.HTMLAttributes<HTMLTableCellElement>) {
  return (
    <td className={cn('p-4 text-sm text-foreground', className)} {...props}>
      {children}
    </td>
  );
}
