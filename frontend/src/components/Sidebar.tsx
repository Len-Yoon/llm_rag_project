// frontend/src/components/Sidebar.tsx
import React from "react";

interface Props {
  history: { id: number; question: string; answer: string }[];
  bookmarks: { id: number; question: string; answer: string }[];
}

const Sidebar: React.FC<Props> = ({ history, bookmarks }) => {
  return (
    <div className="w-64 border-r p-4 overflow-y-auto">
      <h2 className="font-bold mb-2">📜 최근 검색</h2>
      <ul className="mb-4">
        {history.map((h) => (
          <li key={h.id} className="text-sm mb-1">
            {h.question}
          </li>
        ))}
      </ul>
      <h2 className="font-bold mb-2">⭐ 즐겨찾기</h2>
      <ul>
        {bookmarks.map((b) => (
          <li key={b.id} className="text-sm mb-1">
            {b.question}
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Sidebar;
