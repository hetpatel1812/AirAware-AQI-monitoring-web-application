
document.addEventListener('DOMContentLoaded', () => {
    fetchNews();
});

async function fetchNews() {
    const newsGrid = document.getElementById('newsGrid');

    try {
        const response = await fetch('/api/news');
        const data = await response.json();

        if (data.news && data.news.length > 0) {
            renderNews(data.news);
        } else {
            newsGrid.innerHTML = `
                <div class="loading-container">
                    <p>No news available at the moment.</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error fetching news:', error);
        newsGrid.innerHTML = `
            <div class="loading-container">
                <p>Failed to load news. Please try again later.</p>
            </div>
        `;
    }
}

function renderNews(articles) {
    const newsGrid = document.getElementById('newsGrid');
    newsGrid.innerHTML = ''; // Clear loading state

    articles.forEach(article => {
        // Skip articles without titles or images if desired, but let's keep them if possible
        if (!article.title) return;

        const card = document.createElement('div');
        card.className = 'news-card';

        const imageUrl = article.image_url || 'https://images.unsplash.com/photo-1611273426761-53c8577a3c7f?auto=format&fit=crop&q=80&w=500';
        const date = article.pubDate ? new Date(article.pubDate).toLocaleDateString() : 'Recent';
        const source = article.source_id || 'News';

        card.innerHTML = `
            <img src="${imageUrl}" alt="${article.title}" class="news-image" loading="lazy" onerror="this.src='https://images.unsplash.com/photo-1611273426761-53c8577a3c7f?auto=format&fit=crop&q=80&w=500'">
            <div class="news-content">
                <div class="news-source">${source}</div>
                <h3 class="news-title">${article.title}</h3>
                <div class="news-date">
                    <span class="material-symbols-rounded" style="font-size: 16px;">calendar_today</span>
                    ${date}
                </div>
                <p class="news-description">${article.description || 'No description available.'}</p>
                <div class="news-action">
                    <a href="${article.link}" target="_blank" rel="noopener noreferrer" class="read-more-btn">
                        Read Full Story
                        <span class="material-symbols-rounded" style="font-size: 18px;">open_in_new</span>
                    </a>
                </div>
            </div>
        `;

        newsGrid.appendChild(card);
    });
}
