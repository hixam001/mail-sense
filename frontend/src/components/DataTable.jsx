export default function DataTable({ caption, columns, rows, minWidth }) {
  return <div className="table-scroll" role="region" aria-label={caption} tabIndex="0" title="Use arrow keys or scroll horizontally if columns extend beyond the view.">
    <table style={{ minWidth }}><caption>{caption}</caption><thead><tr>{columns.map(column => <th key={column} scope="col">{column}</th>)}</tr></thead>
      <tbody>{rows.map((row, index) => <tr key={index}>{row.map((cell, column) => column === 0 ?
        <th key={column} scope="row">{cell}</th> : <td key={column}>{cell}</td>)}</tr>)}</tbody>
    </table>
  </div>
}
