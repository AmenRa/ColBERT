import grpc
from concurrent import futures
import torch
import server_pb2
import server_pb2_grpc

import os
import gc

import time
import csv

from colbert import Searcher
from collections import defaultdict


class ColBERTServer(server_pb2_grpc.ServerServicer):
    def __init__(self):
        k = 100
        self.index_name = "msmarco.nbits=2.latest.mmap"
        gold_rankings_files = "/data/msmarco.k=1000.device=gpu.ranking.tsv"
        self.gold_ranks = defaultdict(list)

        with open(gold_rankings_files, newline='', encoding='utf-8') as tsvfile:
            tsv_reader = csv.reader(tsvfile, delimiter='\t')
            for line in tsv_reader:
                self.gold_ranks[int(line[0])].append(int(line[1]))

        self.searcher = Searcher(index=f"/data/indexes/{self.index_name}/")
        self.ranker = self.searcher.ranker

    def convert_dict_to_protobuf(self, input_dict):
        query_result = server_pb2.QueryResult()

        query_result.query = input_dict["query"]

        for topk_dict in input_dict["topk"]:
            topk_result = query_result.topk.add()
            topk_result.pid = topk_dict["pid"]
            topk_result.rank = topk_dict["rank"]
            topk_result.score = topk_dict["score"]

        return query_result

    def api_search_query(self, query, qid, k=100):
        gc.collect()
        t2 = time.time()
        pids, ranks, scores = self.searcher.search(query, k)
        print("Searching time of {}: {}".format(qid, time.time() - t2))

        top_k = []
        for pid, rank, score in zip(pids, ranks, scores):
            top_k.append({'pid': pid, 'rank': rank, 'score': score})
        top_k = list(sorted(top_k, key=lambda p: (-1 * p['score'], p['pid'])))

        del pids
        del ranks
        del scores

        return self.convert_dict_to_protobuf({"query": query, "topk": top_k})

    def api_rerank_query(self, query, qid, k=100):
        gc.collect()
        t2 = time.time()
        gr = torch.tensor(self.gold_ranks[qid][:k], dtype=torch.int)
        Q = self.searcher.encode([query])
        # score = ranker.score_raw_pids(config, Q[i:i+1], torch.tensor(list(docs)[:10000], dtype=torch.int))
        scores_, pids_ = self.ranker.score_raw_pids(self.searcher.config, Q, gr)
        print("Reranking time of {}: {}".format(qid, time.time() - t2))
        # times.append(time.time() - t2)

        top_k = []
        for pid, rank, score in zip(pids_, range(len(pids_)), scores_):
            top_k.append({'pid': pid + 1, 'rank': rank, 'score': score})
        top_k = list(sorted(top_k, key=lambda p: (-1 * p['score'], p['pid'])))

        del gr
        del scores_
        del pids_
        del Q

        return self.convert_dict_to_protobuf({"query": query, "topk": top_k})

    def Search(self, request, context):
        torch.set_num_threads(1)
        return self.api_search_query(request.query, request.qid, request.k)

    def Rerank(self, request, context):
        print("Running")
        # print("Running on", os.environ["PROC_NUM"])
        torch.set_num_threads(1)
        return self.api_rerank_query(request.query, request.qid, request.k)


def serve_ColBERT_server():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    server_pb2_grpc.add_ServerServicer_to_server(ColBERTServer(), server)
    listen_addr = '[::]:5005' + str(int(os.environ["PROC_NUM"]))
    server.add_insecure_port(listen_addr)
    print(f"Starting ColBERT server on {listen_addr}")
    server.start()
    server.wait_for_termination()
    print("Terminated")


if __name__ == '__main__':
    serve_ColBERT_server()
