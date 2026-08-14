// StockHunter CORS Proxy Worker (支持 GET + POST)
// 部署到 proxy2.2allanng.workers.dev 覆盖现有
// 用法: https://<worker>/?url=<TARGET_URL_ENCODED>
//   GET: 转发 GET 到 target
//   POST: 转发 POST (含 body) 到 target，支持 form-urlencoded / json body

const ALLOWED_ORIGIN = "*"; // 或更严格: "https://stockhunter.netlify.app"

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const target = url.searchParams.get("url");
    if (!target) {
      return new Response("Missing url param", { status: 400 });
    }

    const init = {
      method: request.method,
      headers: {
        "User-Agent": "Mozilla/5.0",
        "Accept": "*/*",
      },
      redirect: "follow",
    };

    // 转发 body (POST/PUT)
    if (request.method === "POST" || request.method === "PUT") {
      const ct = request.headers.get("content-type") || "application/x-www-form-urlencoded";
      init.headers["Content-Type"] = ct;
      const body = await request.arrayBuffer();
      init.body = body;
    }

    let resp;
    try {
      resp = await fetch(target, init);
    } catch (e) {
      return new Response("Upstream error: " + e.message, { status: 502 });
    }

    // CORS 头
    const headers = new Headers(resp.headers);
    headers.set("Access-Control-Allow-Origin", ALLOWED_ORIGIN);
    headers.set("Access-Control-Allow-Methods", "GET, POST, OPTIONS");
    headers.set("Access-Control-Allow-Headers", "*");

    // 处理预检
    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers });
    }

    return new Response(resp.body, {
      status: resp.status,
      headers,
    });
  },
};
