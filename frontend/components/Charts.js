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
    duration: 320,
    easing: 'easeOutCubic'
  },
  plugins: {
    legend: {
      labels: {
        color: '#dfe2eb'
      }
    }
  },
  scales: {
    x: {
      ticks: { color: 'rgba(223,226,235,0.82)' },
      grid: { color: 'rgba(65,71,85,0.35)' }
    },
    y: {
      ticks: { color: 'rgba(223,226,235,0.82)' },
      grid: { color: 'rgba(65,71,85,0.35)' }
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
              borderColor: '#adc6ff',
              backgroundColor: 'rgba(173,198,255,0.16)',
              fill: true,
              tension: 0.36,
              pointRadius: 3,
              pointBackgroundColor: '#4b8eff'
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
              labels: { color: '#dfe2eb' }
            }
          }
        }}
        data={{
          labels: items.map((item) => item.name),
          datasets: [
            {
              data: items.map((item) => item.value),
              backgroundColor: ['#adc6ff', '#4b8eff', '#7aa2ff', '#6d7f9f', '#4ae176']
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
              backgroundColor: ['#6d7f9f', '#4ae176', '#adc6ff', '#ffb3ad', '#ff8a80']
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
              backgroundColor: '#adc6ff'
            },
            {
              label: 'Correlated Alerts',
              data: secondSeries,
              backgroundColor: '#4b8eff'
            }
          ]
        }}
      />
    </Card>
  );
}
