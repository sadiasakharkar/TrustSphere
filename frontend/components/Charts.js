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
import Card from './Card';

ChartJS.register(ArcElement, CategoryScale, LinearScale, PointElement, LineElement, BarElement, Tooltip, Legend, Filler);

const commonOptions = {
  responsive: true,
  maintainAspectRatio: false,
  animation: {
    duration: 900,
    easing: 'easeOutQuart'
  },
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

export function AnomalyLineChart({ series, title = 'Anomaly Trends Over Time', label = 'Behavioral Risk Index' }) {
  return (
    <Card className="h-[320px]" title={title}>
      <Line
        options={commonOptions}
        data={{
          labels: ['00:00', '02:00', '04:00', '06:00', '08:00', '10:00', '12:00', '14:00', '16:00', '18:00', '20:00', '22:00'],
          datasets: [
            {
              label,
              data: series,
              borderColor: '#00FFFF',
              backgroundColor: 'rgba(0,255,255,0.2)',
              fill: true,
              tension: 0.36,
              pointRadius: 3,
              pointBackgroundColor: '#4FD1C5'
            }
          ]
        }}
      />
    </Card>
  );
}

export function AlertPieChart({ items, title = 'Alert Type Distribution' }) {
  return (
    <Card className="h-[320px]" title={title}>
      <Doughnut
        options={{
          responsive: true,
          maintainAspectRatio: false,
          animation: { duration: 900 },
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
    </Card>
  );
}

export function SeverityBarChart({ values, title = 'Severity Levels' }) {
  return (
    <Card className="h-[320px]" title={title}>
      <Bar
        options={commonOptions}
        data={{
          labels: ['Info', 'Low', 'Medium', 'High', 'Critical'],
          datasets: [
            {
              label: 'Events',
              data: values,
              backgroundColor: ['#40A9FF', '#4FD1C5', '#00FFFF', '#FFA500', '#FF4B4B']
            }
          ]
        }}
      />
    </Card>
  );
}

export function DualSeriesBarChart({ labels, firstSeries, secondSeries, title }) {
  return (
    <Card className="h-[320px]" title={title}>
      <Bar
        options={commonOptions}
        data={{
          labels,
          datasets: [
            {
              label: 'Behavioral Deviations',
              data: firstSeries,
              backgroundColor: '#00FFFF'
            },
            {
              label: 'Correlated Alerts',
              data: secondSeries,
              backgroundColor: '#7F5AF0'
            }
          ]
        }}
      />
    </Card>
  );
}
