import { useEffect, useState } from "react";
import ChatPage from "./pages/ChatPage";
import EvaluationPage from "./pages/EvaluationPage";

const route = () => (window.location.hash.startsWith("#/evaluation") ? "evaluation" : "chat");

export default function App() {
  const [page, setPage] = useState(route);
  useEffect(() => {
    const on = () => setPage(route());
    window.addEventListener("hashchange", on);
    return () => window.removeEventListener("hashchange", on);
  }, []);
  return page === "evaluation" ? <EvaluationPage /> : <ChatPage />;
}
