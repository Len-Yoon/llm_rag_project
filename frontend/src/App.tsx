// frontend/src/App.tsx
import {useEffect, useRef, useState} from "react";
import {ask, clearConversation, stats, type Source} from "./api";

type Status = "idle" | "loading" | "done" | "error";

function newCid() {
    return crypto.randomUUID();
}

export default function App() {
    const [q, setQ] = useState("일본 5500억 달러");
    const [k, setK] = useState(4);
    const [fast, setFast] = useState(false);
    const [cid, setCid] = useState<string>(() => newCid());

    const [answer, setAnswer] = useState("");
    const [sources, setSources] = useState<Source[]>([]);
    const [status, setStatus] = useState<Status>("idle");
    const [err, setErr] = useState<string>("");
    const [count, setCount] = useState<number>(0);

    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        inputRef.current?.focus();
        (async () => {
            try {
                const s = await stats();
                setCount(s?.count ?? 0);
            } catch {
            }
        })();
    }, []);

    const onSearch = async () => {
        const query = q.trim();
        if (!query) return;

        setStatus("loading");
        setErr("");
        setAnswer("");
        setSources([]);

        try {
            const res = await ask({question: query, k, fast, conversation_id: cid});
            if ("error" in res && res.error) setErr(res.error);
            setAnswer(res.answer ?? "");
            setSources(res.contexts ?? []);
            setStatus("done");
            try {
                const s = await stats();
                setCount(s?.count ?? 0);
            } catch {
            }
        } catch (e: any) {
            setErr(e?.response?.data?.message || e?.message || "요청 실패");
            setStatus("error");
        }
    };

    const onNewChat = async () => {
        setStatus("idle");
        setErr("");
        setAnswer("");
        setSources([]);
        const newId = newCid();
        setCid(newId);
        try {
            await clearConversation(newId); // 대화 전용 폴더 초기화(혹시 잔존 데이터 있으면)
        } catch {
        }
    };

    const onKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === "Enter") onSearch();
    };

    return (
        <div className="min-h-screen bg-gray-50 text-gray-900">
            <header className="sticky top-0 z-10 border-b bg-white/70 backdrop-blur">
                <div className="mx-auto flex max-w-4xl items-center gap-3 px-4 py-3">
          <span className="rounded-xl bg-indigo-600 px-2 py-1 text-sm font-semibold text-white">
            Live RAG
          </span>
                    <h1 className="text-lg font-bold">뉴스 검색</h1>
                    <div className="ml-auto flex items-center gap-3 text-xs text-gray-500">
                        <span>API: {import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000"}</span>
                        <span>Vector count: {count}</span>
                        <button
                            onClick={onNewChat}
                            className="rounded-lg border px-2 py-1 font-semibold text-gray-700 hover:bg-gray-100"
                            title="대화별 인덱스를 초기화하고 새로운 conversation_id로 시작"
                        >
                            새 채팅
                        </button>
                    </div>
                </div>
            </header>

            <main className="mx-auto max-w-4xl px-4 py-6">
                <div className="rounded-2xl border bg-white p-4 shadow-sm">
                    <div className="flex flex-col gap-3 sm:flex-row">
                        <div className="flex-1">
                            <label className="mb-1 block text-sm text-gray-600">질문</label>
                            <input
                                ref={inputRef}
                                value={q}
                                onChange={(e) => setQ(e.target.value)}
                                onKeyDown={onKeyDown}
                                placeholder="예) 일본 5500억 달러 환율 개입"
                                className="w-full rounded-xl border px-3 py-2 outline-none ring-indigo-100 focus:ring-2"
                                aria-label="질문 입력"
                            />
                            <p className="mt-1 text-xs text-gray-500">Enter로 검색</p>
                        </div>

                        <div className="w-full sm:w-28">
                            <label className="mb-1 block text-sm text-gray-600">Top-k</label>
                            <select
                                value={k}
                                onChange={(e) => setK(Number(e.target.value))}
                                className="w-full rounded-xl border px-3 py-2 outline-none ring-indigo-100 focus:ring-2"
                                aria-label="Top-k 선택"
                            >
                                {[2, 3, 4, 5, 6, 8].map((n) => (
                                    <option key={n} value={n}>{n}</option>
                                ))}
                            </select>
                        </div>

                        <div className="flex items-end gap-3">
                            <label className="flex select-none items-center gap-2 text-sm text-gray-700">
                                <input
                                    type="checkbox"
                                    checked={fast}
                                    onChange={(e) => setFast(e.target.checked)}
                                    className="h-4 w-4 rounded border-gray-300"
                                />
                                빠른 검색(크롤 생략)
                            </label>

                            <button
                                onClick={onSearch}
                                disabled={status === "loading"}
                                className="inline-flex items-center justify-center rounded-xl bg-indigo-600 px-5 py-2.5 font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:opacity-60"
                                aria-busy={status === "loading"}
                            >
                                {status === "loading" ? (
                                    <svg className="mr-2 h-4 w-4 animate-spin" viewBox="0 0 24 24" fill="none">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor"
                                                strokeWidth="4"/>
                                        <path className="opacity-75" d="M4 12a8 8 0 018-8" stroke="currentColor"
                                              strokeWidth="4" strokeLinecap="round"/>
                                    </svg>
                                ) : null}
                                검색
                            </button>
                        </div>
                    </div>
                </div>

                <section className="mt-6 space-y-4">
                    {err ? (
                        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-red-700">
                            <div className="font-semibold">요청 실패</div>
                            <div className="text-sm whitespace-pre-wrap">{err}</div>
                        </div>
                    ) : null}

                    <div className="rounded-2xl border bg-white p-5 shadow-sm">
                        <div className="mb-2 text-base font-semibold">답변</div>
                        {status === "loading" ? (
                            <div className="space-y-2">
                                <div className="h-3 w-5/6 animate-pulse rounded bg-gray-100"/>
                                <div className="h-3 w-3/4 animate-pulse rounded bg-gray-100"/>
                                <div className="h-3 w-2/3 animate-pulse rounded bg-gray-100"/>
                            </div>
                        ) : (
                            <p className="whitespace-pre-wrap leading-7">{answer}</p>
                        )}
                    </div>

                    {sources.length > 0 && (
                        <div className="rounded-2xl border bg-white p-4 shadow-sm">
                            <div className="mb-3 text-base font-semibold">참고 문서</div>
                            <ul className="space-y-3">
                                {sources.map((s, i) => (
                                    <li key={i} className="rounded-xl border p-3 transition hover:bg-gray-50">
                                        <a
                                            href={s.url}
                                            target="_blank"
                                            rel="noreferrer"
                                            className="font-semibold text-indigo-700 hover:underline"
                                            title={s.title || s.url}
                                        >
                                            {s.title || (() => {
                                                try {
                                                    return new URL(s.url).host
                                                } catch {
                                                    return s.url
                                                }
                                            })()}
                                        </a>
                                        <div className="mt-1 text-xs text-gray-500">
                                            {(() => {
                                                try {
                                                    return new URL(s.url).host
                                                } catch {
                                                    return s.url
                                                }
                                            })()}
                                        </div>
                                        <p className="mt-2 line-clamp-3 text-sm text-gray-700">{s.preview}</p>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </section>
            </main>

            <footer className="mx-auto max-w-4xl px-4 py-8 text-center text-xs text-gray-500">
                CID: <span className="font-mono">{cid}</span>
            </footer>
        </div>
    );
}
