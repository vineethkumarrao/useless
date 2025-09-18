async function testTavily() {
  const apiKey = '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';
  const query = 'test query';

  try {
    const response = await fetch('https://api.tavily.com/search', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        api_key: apiKey,
        query: query,
        search_depth: 'basic',
        max_results: 1,
        include_answer: true,
      }),
    });

    console.log('Status:', response.status);
    if (!response.ok) {
      const errorText = await response.text();
      console.error('Error Response:', errorText);
      return;
    }

    const data = await response.json();
    console.log('Success! Answer:', data.answer);
    console.log('Results:', data.results);
  } catch (error) {
    console.error('Fetch error:', error);
  }
}

testTavily();