export default function Table({ columns, rows, rowKey, renderCell, rowClassName }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-left text-sm">
        <thead className="border-b border-white/10 text-text/70">
          <tr>
            {columns.map((column) => (
              <th key={column} className="px-3 py-2 font-medium">
                {column}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row[rowKey]} className={`border-b border-white/5 transition hover:bg-white/5 ${rowClassName ? rowClassName(row) : ''}`}>
              {columns.map((column) => (
                <td key={`${row[rowKey]}-${column}`} className="px-3 py-3 align-top">
                  {renderCell(row, column)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
