import {
    Chart as ChartJS,
    CategoryScale,
    LinearScale,
    BarElement,
    Title,
    Tooltip,
    Legend,
    PointElement,
    LineElement,
    ArcElement
} from "chart.js";
import { Bar, Scatter } from "react-chartjs-2";

ChartJS.register(
    CategoryScale,
    LinearScale,
    BarElement,
    PointElement,
    LineElement,
    ArcElement,
    Title,
    Tooltip,
    Legend
);

export const BarChart = ({ data, title }) => {
    if (!data || Object.keys(data).length === 0) return null;

    const labels = Object.keys(data);
    const values = Object.values(data);

    const chartData = {
        labels,
        datasets: [
            {
                label: title,
                data: values,
                backgroundColor: "rgba(53, 162, 235, 0.5)",
            },
        ],
    };

    return <Bar options={{ responsive: true, plugins: { legend: { position: "top" }, title: { display: true, text: title } } }} data={chartData} />;
};

export const ScatterChart = ({ x, y, data, title }) => {
    // Expects data to be array of objects
    if (!data) return null;

    const points = data.map(row => ({
        x: row[x],
        y: row[y]
    }));

    const chartData = {
        datasets: [
            {
                label: `${x} vs ${y}`,
                data: points,
                backgroundColor: 'rgba(255, 99, 132, 1)',
            }
        ]
    };

    return <Scatter options={{ responsive: true, plugins: { title: { display: true, text: title } } }} data={chartData} />;
};
