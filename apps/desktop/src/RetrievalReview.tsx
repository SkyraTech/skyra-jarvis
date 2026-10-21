import type { ProposalDetail } from './types';

export default function RetrievalReview({ context }: { context: ProposalDetail['context'] }) {
  const retrieval = context.retrieval;
  if (!retrieval) return null;
  return (
    <details className="retrieval-review" aria-label="Retrieved context evidence">
      <summary>
        Retrieved context: {context.files.length} of {Object.keys(retrieval.input_hashes).length}{' '}
        candidates
      </summary>
      <p>
        {retrieval.algorithm} · {retrieval.scope}. Whole-file selection, protected tests retained.
      </p>
      <small>
        Read task {retrieval.task} · Evidence {retrieval.evidence}
      </small>
      <ul>
        {context.files.map((file) => (
          <li key={file.path}>
            {file.path} · {file.sha256}
            {file.protected ? ' · protected' : ''}
          </li>
        ))}
      </ul>
      <h5>Omitted candidates</h5>
      {retrieval.omitted.length ? (
        <ul>
          {retrieval.omitted.map((file) => (
            <li key={file.path}>
              {file.path}: {file.reason}
            </li>
          ))}
        </ul>
      ) : (
        <p>No candidates omitted.</p>
      )}
      <p>
        Query checksum: {retrieval.query_sha256}. This records local lexical retrieval, not semantic
        search or a complete repository scan.
      </p>
    </details>
  );
}
