// frontend/src/api/client.ts
import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000", // FastAPI 서버 주소
});

export default api;
