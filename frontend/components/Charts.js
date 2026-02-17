import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip
} from 'chart.js';
import { Bar, Doughnut, Line } from 'react-chartjs-2';

ChartJS.register(ArcElement, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Tooltip, Legend, Filler);

const commonOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      labels: {
        color: '#E6EDF3'
      }
    }
  },
  scales: {
    x: {
      ticks: { color: '#E6EDF3' },
      grid: { color: 'rgba(255,255,255,0.08)' }
    },
    y: {
      ticks: { color: '#E6EDF3' },
      grid: { color: 'rgba(255,255,255,0.08)' }
    }
  }
};

export function AnomalyLineChart({ series }) {
  return (
    <div className="card h-[320px] p-4">
      <h3 className="mb-3 text-lg font-semibold text-white">Anomaly Trends</h3>
      <Line
        options={commonOptions}
        data={{
          labels: ['01:00', '03:00', '05:00', '07:00', '09:00', '11:00', '13:00', '15:00', '17:00', '19:00', '21:00', '23:00'],
          datasets: [
            {
              label: 'Behavioral Risk Index',
              data: series,
              borderColor: '#00FFFF',
              backgroundColor: 'rgba(0,255,255,0.2)',
              fill: true,
              tension: 0.35
            }
          ]
        }}
      />
    </div>
  );
}

export function AlertPieChart({ items }) {
  return (
    <div className="card h-[320px] p-4">
      <h3 className="mb-3 text-lg font-semibold text-white">Alert Types</h3>
      <Doughnut
        options={{
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
              labels: { color: '#E6EDF3' }
            }
          }
        }}
        data={{
          labels: items.map((item) => item.name),
          datasets: [
            {
              data: items.map((item) => item.value),
              backgroundColor: ['#00FFFF', '#4FD1C5', '#7F5AF0', '#40A9FF', '#1E88E5']
            }
          ]
        }}
      />
    </div>
  );
}

export function SeverityBarChart({ values }) {
  return (
    <div className="card h-[320px] p-4">
      <h3 className="mb-3 text-lg font-semibold text-white">Severity Distribution</h3>
      <Bar
        options={commonOptions}
        data={{
          labels: ['Info', 'Low', 'Medium', 'High', 'Critical'],
          datasets: [
            {
              label: 'Events',
              data: values,
              backgroundColor: ['#40A9FF', '#4FD1C5', '#00FFFF', '#7F5AF0', '#E53935']
            }
          ]
        }}
      />
    </div>
  );
}
