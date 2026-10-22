-- Run with: sqlite3 -header -column ai_video_compiler.db < verify_anime_directives.sql
-- These queries inspect all anime_action rows. Existing databases may contain extra rows.
PRAGMA integrity_check;
SELECT COUNT(*) AS anime_action_count FROM semantic_directives WHERE archetype='anime_action';
SELECT slot_id, COUNT(*) AS records FROM semantic_directives WHERE archetype='anime_action' GROUP BY slot_id ORDER BY slot_id;
SELECT slot_id, moment_type, COUNT(*) AS records FROM semantic_directives WHERE archetype='anime_action' GROUP BY slot_id, moment_type ORDER BY slot_id, moment_type;
SELECT moment_type, COUNT(*) AS records FROM semantic_directives WHERE archetype='anime_action' GROUP BY moment_type ORDER BY moment_type;
SELECT sub_genre, COUNT(*) AS records FROM semantic_directives WHERE archetype='anime_action' GROUP BY sub_genre ORDER BY sub_genre;
SELECT COUNT(*) AS invalid_lengths FROM semantic_directives WHERE archetype='anime_action' AND (length(directive_id)>64 OR length(archetype)>32 OR length(sub_genre)>32 OR length(slot_id)>32 OR length(moment_type)>32);
SELECT COUNT(*) AS blank_required_fields FROM semantic_directives WHERE archetype='anime_action' AND (trim(directive_id)='' OR trim(prompt_snippet)='' OR trim(negative_snippet)='' OR trim(mechanical_guidance)='');
