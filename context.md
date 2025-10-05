Architecture proposed:
React frontend and Python FastAPI backend.


A modern, production‑oriented plan for generating coherent melodic permutations from a small seed set, morphing between two melodies, filtering with learned models, and exporting to MIDI. This version replaces 2017–2019‑era VAEs/n‑grams with transformer embeddings, symbolic diffusion, and LM‑based scoring.

0) Goals & Scope

Input: 2–50 monophonic seed melodies (MIDI), fixed key K, meter (e.g., 4/4), tempo.

Output: Curated MIDI batches of transformed and interpolated meembeddingslodies with strong tonal and cadential coherence.

Approach: Symbolic operators + alignment (DTW/OT) + transformer/diffusion generation + LM‑based scoring + optional manifold visualization.




Workflow summary:

	1.	Ingest & Normalize
	•	Load MIDI → monophonic extraction → quantize → normalize to key K and scale degrees.
	2.	Phrase Segmentation
	•	Split by rests, cadences, or fixed bars.
	3.	Symbolic Generation (Rule-based)
	•	Apply transformations: transpose, invert, contour reshuffle, rhythmic augment/diminish, ornamentation, Euclidean rhythms.
	•	Enforce tonal/ambitus constraints.
	4.	Deterministic Alignment & Morphing
	•	Use DTW or Optimal Transport to align Melody A and B.
	•	Interpolate intermediate melodies at chosen λ steps.
	5.	Model-Based Generation (Contemporary)
	•	Transformer infilling: condition on A and B tokens with a masked gap, generate plausible middles.
	•	Symbolic diffusion: denoise from A→B while respecting key and ambitus.
	6.	Scoring & Filtering
	•	Rank outputs with transformer LM perplexity.
	•	Apply tonal and cadential checks + voice-leading heuristics.
	•	Select a diverse set using transformer encoder embeddings.
	7.	Embedding & Map (Optional)
	•	Visualize motif space using encoder embeddings reduced with PCA/UMAP.
	8.	Render & Export
	•	Map back to MIDI; add micro-timing (swing), velocity shaping, cadence emphasis.
	•	Save provenance (JSON sidecar with operations, model params, scores).
	9.	CLI Workflow
	•	ingest → gen → morph → infill/diffuse → score → select → render.

	Melody Variation & Interpolation Plan — Contemporary Architecture (Python • music21 + Transformers/Diffusion)

1) Environment & Dependencies

Python ≥ 3.10

Core: music21, numpy, scipy, numba

Symbolic I/O: miditoolkit or mido

Tokenization: miditok (REMI/CP/MuMIDI token schemes)

Transformers: torch, transformers, accelerate, huggingface_hub

Diffusion (symbolic): diffusers (discrete/transformer backends) or project‑specific repos

Alignment: fastdtw, pot (Python Optimal Transport)

Viz (optional): umap-learn, matplotlib

pip install music21 miditoolkit miditok mido numpy scipy numba \
            torch transformers accelerate huggingface_hub diffusers \
            fastdtw pot umap-learn matplotlib

Configure music21 env if needed (synth/MuseScore) via music21.environment.set().

2) Representation & Tokenization

Normalized event (analysis layer): (degree:int, octave:int, dur_quarters:float) within key K for rule‑based ops and scoring features.

Model tokens (generation layer): REMI or CP tokens via miditok (NOTE_ON, TIME_SHIFT, VELOCITY, etc.).

Metadata: {key:K, meter, tempo, ambitus, source_id, ops_applied, token_scheme}.

3) Pipeline Overview (Modern)

Ingest MIDI → Streams (music21).

Monophonize & Quantize to grid (e.g., 1/16).

Key normalization (force to K), extract scale degrees.

Phrase segmentation by rests/cadence or fixed bars.

Symbolic generation (permutation operators; §5).

A↔B morphing: DTW/OT align + interpolate (§6).

Model‑based generation:

Transformer infilling: condition on A…[MASK]…B to generate transitions.

Symbolic diffusion: denoise from A→B with controls.

Scoring & filtering: transformer LM perplexity, tonal/cadential checks (§7).

Dedupe & diversify: embedding clustering from transformer encoder.

Render to MIDI with velocities/micro‑timing; log provenance.

4) Preprocessing (unchanged but strict)

Load, extract melody, quantize; store original onsets for micro‑timing.

Force degrees in K when building analysis features; track ambitus (min/max MIDI) for constraints.

Sketch:

from music21 import converter, key as m21key
s = converter.parse('seed.mid')
mel = s.parts[0].melody()
mel.insert(0, m21key.Key('C'))  # example K=C

5) Symbolic Variation Operators (Composable)

Pitch/interval: diatonic transpose; chromatic inflection (capped); contour‑preserving reshuffle (bounded Kendall‑τ); (partial) inversion; retrograde; motif recombination; passing/neighbor insertion; ornaments; octave lifts/drops.

Rhythm/meter: augmentation/diminution; swing/syncopation; Euclidean redistribution E(k,n); duration multiset permutation; rest injection/elision.

Tonal constraints: cadential targets {1, 2→1, 5→1}; leading‑tone resolution; leap compensation after ≥ P4.

These remain state‑of‑practice; they seed and bracket model generations.

6) Alignment & Morphing (Deterministic)

DTW: align A and B on (degree, duration); interpolate at λ∈[0,1], then snap to K and ambitus.

Optimal Transport: event‑set mapping with cost = pitch diff + α·IOI diff; progress coupling toward B to trace paths.

from fastdtw import fastdtw
_ , path = fastdtw(seqA, seqB, dist=lambda a,b: abs(a[0]-b[0]) + 0.5*abs(a[1]-b[1]))

7) Model‑Based Generation (Contemporary)

7.1 Transformer Infilling (symbolic, MIDI tokens)

Tokenizer: miditok (REMI/CP).

Model: pretrained symbolic transformer (Museformer/Moûsai‑style, or HF checkpoints).

Prompt: [TOKENS(A_prefix)] [MASK × N] [TOKENS(B_suffix)] with control tags (key=K, meter, tempo, ambitus bin).

Decode: nucleus/top‑k with temperature annealing; enforce key/ambitus during post.

7.2 Symbolic Diffusion (discrete tokens)

Backbone: diffusers with transformer UNet over token ids (or specialized repos).

Conditioning: cross‑attend to A and B embeddings; interpolate noise schedule from A→B; classifier‑free guidance for key/ambitus.

Output: denoised token sequence; post‑validate cadences and key.

Either path supersedes VAE interpolation and yields smoother, controllable transitions.

8) Scoring & Filtering (Modern)

Transformer LM perplexity: rank candidates by negative log‑likelihood (lower is better).

Tonal/cadential checks: out‑of‑key penalties; final‑degree constraints.

Voice‑leading heuristics: leap frequency, compensation rules.

Diversity: cosine distance in transformer encoder embeddings; apply determinantal point processes (DPP) or farthest‑point sampling to select diverse set.

(Optional) Diffusion acceptance/score networks to prune low‑quality samples.

9) Embedding & Map (Optional, Updated)

Use transformer encoder embeddings (not hand‑crafted histograms) to map pieces; reduce with PCA/UMAP for curation UIs.

10) MIDI Rendering & Provenance

Map degrees→absolute MIDI in key K; quantize to production grid; re‑introduce micro‑timing (±10–20 ms swing).

Velocity: metrical accent model; ornaments softer; cadence lengthened.

Save JSON sidecar: key, meter, ops, model, decoding params, scores, parents, seeds.

11) Project Structure (updated)

melody-variations/
  data/
    seeds/*.mid
    corpus_optional/*.mid
  outputs/
    midi/
    json/
    tokens/
  src/
    io.py              # MIDI load/save, key handling
    normalize.py       # degree mapping, quantize, phrase split
    tokenize.py        # miditok wrappers (REMI/CP)
    ops_pitch.py       # pitch-level generators
    ops_rhythm.py      # rhythm-level generators
    morph.py           # DTW/OT interpolation
    models/
      infill.py        # transformer prompting/decoding
      diffusion.py     # symbolic diffusion sampling
      scoring.py       # LM perplexity, cadence/tonal filters, diversity
    embed.py           # transformer encoder embeddings + UMAP
    cli.py             # batch entrypoints
  plan.md
  requirements.txt

12) CLI Tasks

ingest: parse seeds → normalized + tokens

gen: run symbolic ops

morph: A↔B via DTW/OT (λ grid)

infill: transformer‑based bridge generation between A and B

diffuse: symbolic diffusion A→B generation

score: LM perplexity + musicality filters

select: diversify with encoder embeddings

render: export curated set to MIDI

map (opt): embed & plot

Example:

python -m src.cli ingest --key C --meter 4/4 --seeds data/seeds/
python -m src.cli gen --limit_per_op 200
python -m src.cli morph --pair A.mid B.mid --lambdas 0.1 0.2 ... 0.9
python -m src.cli infill --pair A.mid B.mid --n 64 --topk 8 --p 0.9
python -m src.cli diffuse --pair A.mid B.mid --n 64 --steps 50
python -m src.cli score --topk_per_op 50 --topk_global 500
python -m src.cli select --global_k 300
python -m src.cli render --out outputs/midi

13) Minimal Pseudocode (modern core)

# ingest
phrases = load_and_normalize('data/seeds/*.mid', key='C')
tokens  = tokenize_batch(phrases, scheme='REMI')

# symbolic seeds
cands = []
for ph in phrases:
    cands += op_transpose(ph, steps=range(-6,7))
    cands += op_inversion(ph, axis='tonic')
    cands += op_contour_reshuffle(ph, max_tau=0.3)
    cands += op_rhythm_augment(ph, factors=[0.5, 2.0])

# deterministic morphs
cands += dtw_interpolate(phrases[0], phrases[1], lambdas=[0.1,0.2,...,0.9])

# model-based
bridges_t = transformer_infill(tokens_A, tokens_B, n=64, controls={'key':'C','meter':'4/4'})
bridges_d = diffusion_bridge(tokens_A, tokens_B, n=64, steps=50)

# score & select
all_cands = cands + decode_tokens(bridges_t+bridges_d)
scores = lm_perplexity(all_cands, model='symbolic-transformer')
keep = select_diverse(all_cands, scores, enc_embed_model='symbolic-transformer-encoder', k=300)

# render
for i, ph in enumerate(keep):
    st = phrase_to_stream(ph, key='C', meter='4/4', tempo=100)
    st.write('midi', fp=f'outputs/midi/take_{i:04d}.mid')

14) Parameter Defaults (Starting Set)

Transpose: ±0..±6 degrees; Inversion axis: tonic; Contour τ ≤ 0.3

Rhythm Euclid: E(3,8), E(5,8) in 4/4; Swing offset: 1/6 beat

Infill decoding: top_k=8, top_p=0.9, temp=0.9, repetition penalty 1.2

Diffusion: 30–100 steps, guidance 1.0–2.0, schedule cosine

Scoring weights: 0.5 LM perplexity, 0.2 tonal penalties, 0.15 cadence, 0.15 voice‑leading

15) Acceptance Criteria

≥90% of kept melodies pass key & cadence checks.

Audible A→B continuity for ≥80% of generated bridges.

Diversity: pairwise encoder‑embedding cosine < 0.85 for selected set.

No melody exceeds seed ambitus unless explicitly allowed.

16) Notes on Legacy Components

MusicVAE and n‑gram scoring are retained only for comparison/ablation (optional). The primary paths are transformer infilling and symbolic diffusion.

