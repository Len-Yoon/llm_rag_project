// frontend/src/components/QueryBox.tsx
import React, { useState } from "react";

interface Props {
  onQuery: (question: string) => void;
}

const QueryBox: React.FC<Props> = ({ onQuery }) => {
  const [q, setQ] = useState("");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (q.trim()) {
      onQuery(q);
      setQ("");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 flex gap-2">
      <input
        value={q}
        onChange={(e) => setQ(e.target.value)}
        placeholder="질문을 입력하세요..."
        className="flex-1 border rounded px-3 py-2"
      />
      <button type="submit" className="bg-blue-600 text-white px-4 rounded">
        검색
      </button>
    </form>
  );
};

export default QueryBox;
