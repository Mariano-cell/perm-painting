// netlify/functions/reviews.js

// const CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24h
// let cache = { ts: 0, data: null };

// exports.handler = async (event) => {
//     try {
//         if (event.httpMethod !== "GET") {
//             return {
//                 statusCode: 405,
//                 headers: { "Content-Type": "text/plain" },
//                 body: "Method Not Allowed",
//             };
//         }

//         const apiKey = process.env.GOOGLE_PLACES_API_KEY;
//         const placeId = process.env.PERMA_PLACE_ID;

//         if (!apiKey || !placeId) {
//             return {
//                 statusCode: 500,
//                 headers: { "Content-Type": "application/json" },
//                 body: JSON.stringify({
//                     error: "Missing env vars",
//                     missing: {
//                         GOOGLE_PLACES_API_KEY: !apiKey,
//                         PERMA_PLACE_ID: !placeId,
//                     },
//                 }),
//             };
//         }

//         // Simple in-memory cache
//         const now = Date.now();
//         if (cache.data && now - cache.ts < CACHE_TTL_MS) {
//             return {
//                 statusCode: 200,
//                 headers: {
//                     "Content-Type": "application/json",
//                     "Cache-Control": "public, max-age=3600",
//                 },
//                 body: JSON.stringify(cache.data),
//             };
//         }

//         const fields = "name,rating,user_ratings_total,reviews,url";
//         const url =
//             "https://maps.googleapis.com/maps/api/place/details/json" +
//             `?place_id=${encodeURIComponent(placeId)}` +
//             `&fields=${encodeURIComponent(fields)}` +
//             `&language=en` +
//             `&key=${encodeURIComponent(apiKey)}`;

//         const resp = await fetch(url);
//         const json = await resp.json();

//         if (json.status !== "OK") {
//             return {
//                 statusCode: 502,
//                 headers: { "Content-Type": "application/json" },
//                 body: JSON.stringify({
//                     error: "Places API error",
//                     status: json.status,
//                     details: json.error_message || null,
//                 }),
//             };
//         }

//         const result = {
//             place: {
//                 name: json.result?.name ?? null,
//                 rating: json.result?.rating ?? null,
//                 total: json.result?.user_ratings_total ?? null,
//                 url: json.result?.url ?? null,
//             },
//             reviews: (json.result?.reviews ?? []).slice(0, 5).map((rev) => ({
//                 author_name: rev.author_name,
//                 rating: rev.rating,
//                 relative_time_description: rev.relative_time_description,
//                 text: rev.text,
//                 time: rev.time,
//                 profile_photo_url: rev.profile_photo_url,
//                 author_url: rev.author_url,
//             })),
//             fetched_at: new Date().toISOString(),
//         };

//         cache = { ts: now, data: result };

//         return {
//             statusCode: 200,
//             headers: {
//                 "Content-Type": "application/json",
//                 "Cache-Control": "public, max-age=3600",
//             },
//             body: JSON.stringify(result),
//         };
//     } catch (err) {
//         return {
//             statusCode: 500,
//             headers: { "Content-Type": "application/json" },
//             body: JSON.stringify({
//                 error: "Unhandled error",
//                 message: err?.message || String(err),
//             }),
//         };
//     }
// };


exports.handler = async () => {
    return {
      statusCode: 200,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ok: true }),
    };
  };
  