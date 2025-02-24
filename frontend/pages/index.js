import { useEffect, useState } from "react";

export default function Home() {
  const [articles, setArticles] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchNews = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/news`, {
          headers: {
            "Content-Type": "application/json"
          }
        });

        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const data = await response.json();
        setArticles(data);
      } catch (err) {
        setError("Failed to fetch news. Please try again later.");
        console.error("Error fetching news:", err);
      }
    };

    fetchNews();
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 p-4">
      <h1 className="text-3xl font-bold text-center mb-4">Latest News</h1>
      <div className="max-w-4xl mx-auto space-y-4">
        {error ? (
          <p className="text-center text-red-500">{error}</p>
        ) : articles.length > 0 ? (
          articles.map((article) => (
            <div key={article.id} className="bg-white shadow-md p-4 rounded-lg">
              <h2 className="text-xl font-semibold">{article.title}</h2>
              <p className="text-gray-700">{article.content}</p>
              <a
                href={article.source_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-500 hover:underline"
              >
                Read More
              </a>
            </div>
          ))
        ) : (
          <p className="text-center text-gray-500">Loading news...</p>
        )}
      </div>
    </div>
  );
}

