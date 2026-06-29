exports.handler = async function (event, context) {
    const PLACE_ID = 'ChIJvRmc7caPkGsRkzqug2m9w58';
    const API_KEY = process.env.GOOGLE_PLACES_API_KEY;

    // Places API (New): el endpoint legacy (maps/api/place/details/json) devuelve
    // NOT_FOUND para este perfil de "area de servicio". La API nueva si lo encuentra.
    const url = `https://places.googleapis.com/v1/places/${PLACE_ID}`;

    try {
        const response = await fetch(url, {
            headers: {
                "X-Goog-Api-Key": API_KEY,
                // Pedimos solo los campos que necesitamos (controla el costo)
                "X-Goog-FieldMask": "rating,reviews"
            }
        });
        const data = await response.json();

        if (!response.ok || data.error) {
            return {
                statusCode: 500,
                body: JSON.stringify({
                    error: (data.error && data.error.message) || 'Error en Google API',
                    status: (data.error && data.error.status) || response.status,
                    hasApiKey: Boolean(API_KEY)
                })
            };
        }

        // La API nueva devuelve las reviews con otra estructura. Las mapeamos al
        // formato que ya espera el frontend (author_name, rating, text).
        const reviews = (data.reviews || []).map((rev) => ({
            author_name: (rev.authorAttribution && rev.authorAttribution.displayName) || "",
            rating: rev.rating || 0,
            text: (rev.text && rev.text.text) || (rev.originalText && rev.originalText.text) || ""
        }));

        return {
            statusCode: 200,
            headers: {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            body: JSON.stringify(reviews)
        };
    } catch (error) {
        return {
            statusCode: 500,
            body: JSON.stringify({ error: 'Fallo al conectar con Google' })
        };
    }
};
