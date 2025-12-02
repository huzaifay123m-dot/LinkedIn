// --- AGENT 2: Qualification Agent (LLM Reasoning) ---
async function qualificationAgent(leadData) {
    agent2Output.classList.remove('opacity-50');
    agent2Status.textContent = `🧠 Analyzing data for "${leadData.name}" using Gemini...`;

    // 1. Define the System Instruction (Persona & Rules)
    const systemPrompt = (
        "You are a Senior B2B Lead Qualification Specialist. "
        "Your goal is to analyze the provided company information and determine if they are a 'High-Value Lead' (HV), "
    "a 'Medium-Value Lead' (MV), or a 'Low-Value Lead' (LV). "
    "Base your decision ONLY on whether the company is growing, actively hiring for AI/Tech roles, "
    "and shows clear signs of investment or digital transformation (funding, new product launches). "
    "Provide only a single JSON object."
    );

    // 2. Define the Structured Output Schema
    const schema = {
        "type": "OBJECT",
        "properties": {
            "qualification_level": { "type": "STRING", "description": "HV, MV, or LV" },
            "justification": { "type": "STRING", "description": "A concise reason for the qualification based on growth/hiring/funding evidence." }
        },
        "propertyOrdering": ["qualification_level", "justification"]
    };

    // 3. Define the User Query (The Content to Analyze)
    const leadSummary = Object.entries(leadData)
        .map(([key, value]) => `${key.replace('_', ' ').charAt(0).toUpperCase() + key.slice(1).replace(/_/g, ' ')}: ${value}`)
        .join('\n');
    const userQuery = `Qualify the following lead based on the criteria: \n\n${leadSummary}`;

    // 4. Construct the API Payload
    const payload = {
        contents: [{ parts: [{ text: userQuery }] }],
        systemInstruction: { parts: [{ text: systemPrompt }] },
        generationConfig: {
            responseMimeType: "application/json",
            responseSchema: schema
        }
    };

    // 5. Call the API with Exponential Backoff
    const maxRetries = 5;
    for (let attempt = 0; attempt < maxRetries; attempt++) {
        try {
            const response = await fetch(`${API_URL}?key=${API_KEY}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                const result = await response.json();
                const jsonText = result.candidates?.[0]?.content?.parts?.[0]?.text;

                if (!jsonText) {
                    throw new Error("API returned an empty response body or content structure is invalid.");
                }

                const qualification = JSON.parse(jsonText);

                agent2Status.textContent = '✅ Structured qualification received and parsed.';
                return qualification;

            } else if (response.status === 429 || response.status >= 500) {
                if (attempt < maxRetries - 1) {
                    const sleepTime = (2 ** attempt) * 1000 + Math.random() * 1000;
                    agent2Status.textContent = `⚠️ API error (${response.status}). Retrying in ${(sleepTime / 1000).toFixed(2)}s...`;
                    await new Promise(resolve => setTimeout(resolve, sleepTime));
                    continue;
                } else {
                    throw new Error(`API call failed after ${maxRetries} attempts: ${response.status} - ${await response.text()}`);
                }
            } else {
                throw new Error(`Non-retryable API error: ${response.status} - ${await response.text()}`);
            }

        } catch (error) {
            console.error("Gemini API Error:", error);
            agent2Status.textContent = `❌ Qualification Failed: ${error.message || 'Check console for details.'}`;
            showMessage(`Qualification Failed: ${error.message || 'API request failed.'}`);
            return null;
        }
    }
    return null;
}