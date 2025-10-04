// frontend/src/components/ResultCard.tsx
import React from "react";

interface Props {
  answer: string;
  contexts: string[];
  onBookmark: () => void;
}

const ResultCard: React.FC<Props> = ({ answer, contexts, onBookmark }) => {
  return (
    <div className="p-4 border rounded mb-4 shadow">FFF
      <div className="flex justify-between items-center mb-2">
        <h2 className="text-lg font-bold">AI 답변</h2>
        <button
          onClick={onBookmark}
          className="text-yellow-500 hover:text-yellow-700"
        >
          ⭐ 북마크
        </button>
      </div>
      <p className="mb-3 whitespace-pre-line">{answer}</p>
      <div>
        <h3 className="font-semibold">출처</h3>
        <ul className="list-disc pl-5">
          {contexts.map((c, idx) => (
            <li key={idx}>
              <a href={c} target="_blank" rel="noopener noreferrer" className="text-blue-600">
                {c}
              </a>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
};

export default ResultCard;
