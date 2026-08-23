import { client } from "./client.js";

export async function signUp(username, password) {
  const res = await client.post("/auth/signup", { username, password });
  return res.data;
}

export async function logIn(username, password) {
  const res = await client.post("/auth/login", { username, password });
  return res.data;
}

export async function getMe() {
  const res = await client.get("/auth/me");
  return res.data;
}
