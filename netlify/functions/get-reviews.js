const fetch = require('node-fetch');

exports.handler = async function (event, context) {
    // Reemplaza esto con tu Place ID real
    const PLACE_ID = 'ChIJvRmc7caPkGsRkzqug2m9w58';
    const API_KEY = process.env.GOOGLE_PLACES_API_KEY;

    const url = `https://maps.googleapis.com/maps/api/place/details/json?place_id=${PLACE_ID}&fields=reviews,rating&key=${API_KEY}`;

    try {
        const response = await fetch(url);
        const data = await response.json();

        if (data.status !== 'OK') {
            return {
                statusCode: 500,
                body: JSON.stringify({ error: data.status_message || 'Error en Google API' })
            };
        }

        return {
            statusCode: 200,
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data.result.reviews || [])
        };
    } catch (error) {
        return {
            statusCode: 500,
            body: JSON.stringify({ error: 'Fallo al conectar con Google' })
        };
    }
};