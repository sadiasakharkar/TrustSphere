import { Fragment, useState } from 'react';

export default function DataTable({ columns, rows, getRowKey, renderCell, renderExpandedRow, emptyMessage = 'No records available.' }) {
  const [openRow, setOpenRow] = useState(null);

  if (!rows.length) {
    return <div className="soc-empty min-h-[160px]"><p className="text-sm">{emptyMessage}</p></div>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="soc-table min-w-full">
        <thead>
          <tr>
            {columns.map((column) => <th key={column.key}>{column.label}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => {
            const key = getRowKey(row);
            const expanded = key === openRow;
            return (
              <Fragment key={key}>
                <tr className="soc-table-row cursor-pointer" onClick={() => setOpenRow(expanded ? null : key)}>
                  {columns.map((column) => <td key={`${key}-${column.key}`}>{renderCell(row, column.key)}</td>)}
                </tr>
                {expanded && renderExpandedRow ? (
                  <tr>
                    <td colSpan={columns.length} className="border-b border-[rgba(65,71,85,0.3)] bg-[rgba(16,20,26,0.55)] px-4 py-4">
                      {renderExpandedRow(row)}
                    </td>
                  </tr>
                ) : null}
              </Fragment>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
