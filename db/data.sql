-- Placeholder for benchmark_results data exports.
-- Replace this file with:
--   bash db/dump.sh
-- when you need to share the latest rows with the rest of the team.
--
-- The TRUNCATE ensures a clean slate before inserting, so this file is safe to re-run.
TRUNCATE TABLE benchmark_results RESTART IDENTITY;
TRUNCATE TABLE image_vectors RESTART IDENTITY;

--
-- PostgreSQL database dump
--

\restrict FFdtsEWNQLv4eRDYP0GaGlKBhad5bQnZdxIlvsRJNq6t8CRc96vo4gia4KJ8kvd

-- Dumped from database version 16.13 (Debian 16.13-1.pgdg13+1)
-- Dumped by pg_dump version 16.13 (Debian 16.13-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Data for Name: benchmark_results; Type: TABLE DATA; Schema: public; Owner: qvs
--

COPY public.benchmark_results (id, recorded_at, query_id, engine_name, dimension, target_ids, top_ids, accuracy, state_prep_ms, search_ms, total_ms, parameters, dataset_size, circuit_depth, num_qubits) FROM stdin;
1	2026-03-16 22:28:10.320882+00	query_car	vector_mock_cosine	64	["car_01"]	["car_01", "robot_04", "planet_02"]	1	0	0.08999000056064688	0.1855850023275707	{"top_k": 3, "dimension": 64}	4	\N	\N
2	2026-03-16 22:28:10.331405+00	query_car	quantum_mock_sampler	64	["car_01"]	["car_01", "robot_04", "planet_02"]	1	0.20233000032021664	0.15522900139330886	0.3575590017135255	{"shots": 2048, "top_k": 3, "layers": 2, "dimension": 64}	4	4	2
3	2026-03-16 22:28:10.334405+00	query_planet	vector_mock_cosine	64	["planet_02"]	["planet_02", "robot_04", "car_01"]	1	0	0.07384499986073934	0.15273299868567847	{"top_k": 3, "dimension": 64}	4	\N	\N
4	2026-03-16 22:28:10.337443+00	query_planet	quantum_mock_sampler	64	["planet_02"]	["planet_02", "robot_04", "car_01"]	1	0.08132800212479196	0.0983139980235137	0.17964200014830567	{"shots": 2048, "top_k": 3, "layers": 2, "dimension": 64}	4	4	2
5	2026-03-16 22:28:10.340175+00	query_forest	vector_mock_cosine	64	["forest_03"]	["car_01", "forest_03", "planet_02"]	0.66	0	0.07259099947987124	0.15053899915073998	{"top_k": 3, "dimension": 64}	4	\N	\N
6	2026-03-16 22:28:10.343076+00	query_forest	quantum_mock_sampler	64	["forest_03"]	["car_01", "forest_03", "planet_02"]	0.66	0.07561800157418475	0.09948799925041385	0.1751060008245986	{"shots": 2048, "top_k": 3, "layers": 2, "dimension": 64}	4	4	2
7	2026-03-16 22:28:10.345893+00	query_robot	vector_mock_cosine	64	["robot_04"]	["robot_04", "forest_03", "planet_02"]	1	0	0.06665099863312207	0.13641199620906264	{"top_k": 3, "dimension": 64}	4	\N	\N
8	2026-03-16 22:28:10.348503+00	query_robot	quantum_mock_sampler	64	["robot_04"]	["robot_04", "forest_03", "planet_02"]	1	0.07014999937382527	0.08328999683726579	0.15343999621109106	{"shots": 2048, "top_k": 3, "layers": 2, "dimension": 64}	4	4	2
9	2026-03-16 22:28:10.351226+00	query_car	vector_mock_cosine	128	["car_01"]	["car_01", "planet_02", "robot_04"]	1	0	0.23628199778613634	0.3151860000798479	{"top_k": 3, "dimension": 128}	4	\N	\N
10	2026-03-16 22:28:10.353752+00	query_car	quantum_mock_sampler	128	["car_01"]	["car_01", "planet_02", "robot_04"]	1	0.06487599966931157	0.06728500011377037	0.13216099978308193	{"shots": 2048, "top_k": 3, "layers": 2, "dimension": 128}	4	4	2
11	2026-03-16 22:28:10.35603+00	query_planet	vector_mock_cosine	128	["planet_02"]	["planet_02", "robot_04", "forest_03"]	1	0	0.04668900146498345	0.1049350030370988	{"top_k": 3, "dimension": 128}	4	\N	\N
12	2026-03-16 22:28:10.358897+00	query_planet	quantum_mock_sampler	128	["planet_02"]	["planet_02", "robot_04", "forest_03"]	1	0.059996000345563516	0.06096699871704914	0.12096299906261265	{"shots": 2048, "top_k": 3, "layers": 2, "dimension": 128}	4	4	2
13	2026-03-16 22:28:10.362122+00	query_forest	vector_mock_cosine	128	["forest_03"]	["forest_03", "planet_02", "car_01"]	1	0	0.07822499901521951	0.18221899881609716	{"top_k": 3, "dimension": 128}	4	\N	\N
14	2026-03-16 22:28:10.364851+00	query_forest	quantum_mock_sampler	128	["forest_03"]	["forest_03", "planet_02", "car_01"]	1	0.08468899977742694	0.08903599882614799	0.17372499860357493	{"shots": 2048, "top_k": 3, "layers": 2, "dimension": 128}	4	4	2
15	2026-03-16 22:28:10.367342+00	query_robot	vector_mock_cosine	128	["robot_04"]	["robot_04", "forest_03", "planet_02"]	1	0	0.06433599992305972	0.14367000039783306	{"top_k": 3, "dimension": 128}	4	\N	\N
16	2026-03-16 22:28:10.369682+00	query_robot	quantum_mock_sampler	128	["robot_04"]	["robot_04", "forest_03", "planet_02"]	1	0.057999001001007855	0.055963999329833314	0.11396300033084117	{"shots": 2048, "top_k": 3, "layers": 2, "dimension": 128}	4	4	2
\.


--
-- Name: benchmark_results_id_seq; Type: SEQUENCE SET; Schema: public; Owner: qvs
--

SELECT pg_catalog.setval('public.benchmark_results_id_seq', 16, true);


--
-- PostgreSQL database dump complete
--

\unrestrict FFdtsEWNQLv4eRDYP0GaGlKBhad5bQnZdxIlvsRJNq6t8CRc96vo4gia4KJ8kvd

