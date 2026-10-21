import { useId } from 'react';

export type SkillChoice = { name: string; version: string; sha256: string };
export type SkillSelection = Record<string, string>;

export function skillsAreCurrent(available: SkillChoice[], selected: SkillSelection) {
  return Object.entries(selected).every(([name, sha256]) =>
    available.some((skill) => skill.name === name && skill.sha256 === sha256),
  );
}

/** Selected hashes remain pinned until the owner explicitly selects updated guidance. */
export default function TrustedSkills({
  available,
  selected,
  onChange,
  disabled = false,
}: {
  available: SkillChoice[];
  selected: SkillSelection;
  onChange: (value: SkillSelection) => void;
  disabled?: boolean;
}) {
  const help = useId();
  const names = Object.keys(selected);
  const missing = names.filter((name) => !available.some((skill) => skill.name === name));
  function remove(name: string) {
    const value = { ...selected };
    delete value[name];
    onChange(value);
  }
  return (
    <fieldset className="trusted-skills wide" aria-describedby={help} disabled={disabled}>
      <legend>Trusted coding guidance · optional</legend>
      <p id={help}>
        Choose up to five skills. Guidance shapes the model response; project permissions still
        control actions.
      </p>
      {!available.length && <p>No trusted skills are registered in the host configuration.</p>}
      {available.map((skill) => {
        const checked = Object.hasOwn(selected, skill.name);
        const changed = checked && selected[skill.name] !== skill.sha256;
        return (
          <label className="checkbox skill-choice" key={skill.name}>
            <input
              type="checkbox"
              checked={checked}
              aria-label={`Use skill ${skill.name}`}
              disabled={!checked && names.length >= 5}
              onChange={(event) =>
                event.target.checked
                  ? onChange({ ...selected, [skill.name]: skill.sha256 })
                  : remove(skill.name)
              }
            />
            <span>
              <strong>{skill.name}</strong> · {skill.version}
              <small title={skill.sha256}>
                Revision {skill.sha256.slice(0, 12)}
                {changed && ' · Changed since selection; select it again.'}
              </small>
            </span>
          </label>
        );
      })}
      {missing.map((name) => (
        <p key={name}>
          Unavailable skill: {name}{' '}
          <button type="button" onClick={() => remove(name)}>
            Remove {name}
          </button>
        </p>
      ))}
      {!skillsAreCurrent(available, selected) && (
        <p className="error-text" role="alert">
          Selected guidance changed. Review and select the current revision before continuing.
        </p>
      )}
    </fieldset>
  );
}
