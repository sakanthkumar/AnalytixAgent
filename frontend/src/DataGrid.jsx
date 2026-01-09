import { useState, useEffect } from 'react';
import axios from 'axios';

export default function DataGrid({ onClose }) {
    const [data, setData] = useState([]);
    const [columns, setColumns] = useState([]);
    const [page, setPage] = useState(1);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(false);
    const limit = 50;

    useEffect(() => {
        const fetchData = async () => {
            setLoading(true);
            try {
                const res = await axios.get(`http://localhost:8000/data?page=${page}&limit=${limit}`);
                if (res.data.data && res.data.data.length > 0) {
                    setData(res.data.data);
                    setColumns(Object.keys(res.data.data[0]));
                    setTotal(res.data.total_rows);
                }
            } catch (e) {
                console.error(e);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [page]);

    return (
        <div className="modal-overlay">
            <div className="modal-content">
                <header className="modal-header">
                    <h2>Dataset Viewer ({total} rows)</h2>
                    <button onClick={onClose} className="close-btn">Close</button>
                </header>

                <div className="table-wrapper grid-table">
                    {loading ? <div className="spinner"></div> : (
                        <table>
                            <thead>
                                <tr>
                                    {columns.map(col => <th key={col}>{col}</th>)}
                                </tr>
                            </thead>
                            <tbody>
                                {data.map((row, i) => (
                                    <tr key={i}>
                                        {columns.map(col => <td key={col}>{row[col]}</td>)}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    )}
                </div>

                <div className="pagination">
                    <button disabled={page === 1} onClick={() => setPage(p => p - 1)}>Previous</button>
                    <span>Page {page}</span>
                    <button disabled={page * limit >= total} onClick={() => setPage(p => p + 1)}>Next</button>
                </div>
            </div>
        </div>
    );
}
