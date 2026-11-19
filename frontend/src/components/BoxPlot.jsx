import DataTable from './DataTable.jsx'
import { NumberValue } from './common.jsx'

export default function BoxPlot({ values, unit }) {
  if (!values) return <p className="note">No numeric observations in this selection.</p>
  const x = value => values.max === values.min ? 250 : 30 + 440 * (value - values.min) / (values.max - values.min)
  return <>
    <svg className="boxplot" viewBox="0 0 500 100" role="img" aria-label={`Five-number box plot in ${unit}; exact values in the table below`}>
      <line x1={x(values.min)} x2={x(values.max)} y1="45" y2="45" />
      <rect x={x(values.q1)} y="25" width={Math.max(1, x(values.q3) - x(values.q1))} height="40" />
      {[values.min, values.median, values.max].map((value, i) => <line key={i} x1={x(value)} x2={x(value)} y1="20" y2="70" />)}
      <text x="30" y="95">Minimum</text><text x="470" y="95" textAnchor="end">Maximum</text>
    </svg>
    <DataTable caption={`Five-number summary · ${unit}`} columns={['Statistic', 'Value']}
      rows={Object.entries(values).map(([label, value]) => [label, <NumberValue key={label} value={value} />])} />
    <p className="note">Whiskers show the minimum and maximum, not Tukey outlier fences. A long tail can compress the box.</p>
  </>
}
