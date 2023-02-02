import argparse
import copy
import gc
import matplotlib.pyplot
import random
import os, psutil
from multiprocessing import Process, Queue
import sys
import time
import torch

HDD_filepath = '/lfs/1/udingank/msmarco.nbits-2.latest'
SSD_filepath = '/lfs/0/udingank/msmarco.nbits-2.latest'
Sources = [HDD_filepath, SSD_filepath]
Results = ['results-hdd.png', 'results-ssd.png']

#Sources = [TestFile]
#Results = ['results.png']
#TestFile = os.path.join('./colbert/tests', 'mmap_test_data.pt')
#TEST_FILE_SIZE = 1209306560

verbose = False

TEST_CHUNK_SIZE = 100000
BYTE_SIZE = 1

NUM_COMPUTE_CYCLES = 10

NUM_RES_FILES = 50
#NUM_RES_FILES = 354
TensorSizes = [51166240, 51453472, 50933984, 52260032, 54481664, 54507104, 53236320, 53662720, 53944384, 54002784, 53552256, 53667328, 54137248, 54020352, 54441184, 53984192, 53614432, 54481120, 54064096, 54103616, 54155040, 54032160, 53146528, 53839648, 53485664, 54296672, 53755040, 54010784, 54191008, 53782240, 54119968, 53886496, 54510016, 54021184, 53680544, 54164352, 54120192, 54463776, 54394944, 53432672, 54699488, 53804480, 54014720, 53671136, 54194016, 53839008, 54290848, 54043008, 53700608, 53871520, 53178624, 53900512, 54015904, 54518592, 54416992, 54581504, 54298848, 54158368, 54041568, 54378688, 53839232, 54287264, 54091488, 53730464, 53566848, 54063168, 53944000, 54137632, 53897248, 53624928, 54485760, 54331104, 54647968, 54599968, 54546112, 53670656, 53914016, 54217856, 54305568, 54257984, 55005792, 53951104, 54497792, 54992992, 53889312, 53944960, 54473152, 54046304, 54046592, 53580608, 53617120, 53198688, 52915296, 53923072, 53460608, 53548960, 53694048, 52599968, 53268992, 53557248, 53561184, 53765344, 53556928, 54078720, 53031232, 52926656, 53063488, 53754752, 53772832, 53557376, 53072832, 53428576, 53395040, 53273056, 54276864, 54657504, 54099744, 54236448, 53307712, 54159072, 53775136, 53634304, 54093600, 53819488, 53801952, 53867648, 53353184, 54316416, 53560160, 54134944, 54071040, 53986240, 53095328, 54027392, 53961152, 54152192, 54478080, 53665952, 54025856, 54155104, 53544480, 54216288, 53941088, 54007232, 54223584, 54205568, 54400512, 54376128, 53829888, 53570272, 54360640, 54483200, 54144544, 54127840, 54259968, 54754080, 54135424, 54396256, 54146272, 54016480, 53712160, 54274944, 53699328, 54432928, 53947104, 54777440, 54762560, 54062240, 53732000, 54165472, 53983008, 54270240, 53841184, 54049632, 54479584, 54213408, 54072352, 54254080, 54023808, 53854048, 54086080, 53979232, 54049760, 54452224, 54038432, 54250400, 54175200, 53975360, 53975040, 54322240, 54386976, 54497344, 54133696, 54680224, 54133280, 54353952, 53630944, 54746432, 54309952, 54326304, 53676640, 53812832, 54615200, 54287328, 54299040, 54149728, 54295104, 54523104, 54241568, 54858880, 54318496, 54335744, 54264544, 54396960, 53915104, 54295488, 54525600, 53891296, 56159488, 55877920, 56103040, 55800384, 56200736, 56150944, 56126624, 56212480, 55750496, 56334304, 56007040, 55243040, 56307488, 56544448, 56301600, 56649344, 56383232, 55934720, 56568160, 55167168, 55105696, 55868096, 56705792, 56838944, 56551680, 55503584, 55104064, 55028000, 68795968, 68374464, 69128096, 69118464, 69394560, 69144544, 65822272, 55919712, 55927488, 55884064, 56379936, 56346112, 56495008, 56287936, 56274688, 56749184, 55768384, 55717088, 56645696, 56226848, 55737824, 54995168, 55074272, 54782976, 54654656, 54770304, 55382976, 54883168, 54950880, 54718720, 54119136, 54758240, 54616160, 54621824, 54731488, 54192096, 54766080, 48401120, 49150912, 49069664, 49203360, 49278720, 49314432, 49361312, 48923936, 49091264, 54095776, 54359104, 55029088, 54100160, 53178976, 52473120, 52235616, 52540064, 52655776, 52533696, 52408640, 52615104, 52067776, 52357344, 52091520, 52763392, 52244512, 51152224, 51657984, 51895904, 52145440, 51986272, 51948480, 52014336, 51195552, 51687200, 51962720, 53245056, 52912096, 48251168, 49227872, 49226176, 48693184, 49111040, 49186496, 49182912, 47979776, 51783904, 54250272, 54625472, 55362592, 53950944, 52790720, 53113216, 52760768, 52939264, 52933216, 52595296, 52696064, 52492320, 52494240, 52527264, 52841952, 52392256, 51322752, 51423200, 51795936, 51569760, 51588672, 52201760, 51910304, 34766720]
TEST_FILE_SIZE = sum(TensorSizes)

B_PER_GB = 1e9

control_basic = []
mmap_basic = []
control_compute = []
mmap_compute = []

control_timing = []
mmap_timing = []

def read_residuals(mmap, filepath, proc, q):
    mem_buf = []

    for i in range(NUM_RES_FILES):
        filename = os.path.join(filepath, "{}.residuals.pt".format(i))

        if (i % 10 == 0):
            if verbose: print("reading file {}".format(filename))

        if mmap:
            storage = torch.ByteStorage.from_file(filename, shared=False, size=TensorSizes[i])

        if mmap:
            mem_buf.append(torch.ByteTensor(storage))
        else:
            mem_buf.append(torch.load(filename, map_location='cpu'))

    mem = proc.memory_info().rss/B_PER_GB
    q.put(mem)

    return mem_buf

def read_into_buffer(mmap, filepath, q):
    proc = psutil.Process(os.getpid())

    # read time, average copy time, average calculation time, total time
    timing = { 'read_time': 0, 'average_copy_time': 0, 'average_calc_time': 0, 'total_time': 0 }

    # read from residual files into mem_buf
    start_time = time.time()
    mem_buf = read_residuals(mmap, filepath, proc, q)

    fetch_time = time.time()

    copy_avg = 0
    calc_avg = 0
    results_buf = []

    for i in range(NUM_COMPUTE_CYCLES):
        if (i % 10 == 0):
            print("copying cycle {}".format(i))

        rand_time_start = time.time()

        res = random.randrange(0, NUM_RES_FILES)
        res_size = TensorSizes[res]
        start = random.randrange(res_size - TEST_CHUNK_SIZE)
        end = min(start + TEST_CHUNK_SIZE, res_size)
        temp = mem_buf[res][start:end]

        new_buf = copy.deepcopy(temp)

        del temp
        gc.collect()

        ts1 = time.time()
        computation = torch.sum(new_buf)
        ts2 = time.time()

        copy_avg += ts1 - rand_time_start
        calc_avg += ts2 - ts1

        mem = proc.memory_info().rss/B_PER_GB
        results_buf.append(mem)

        del new_buf
        gc.collect()

    end_time = time.time()

    copy_avg = copy_avg/NUM_COMPUTE_CYCLES
    calc_avg = calc_avg/NUM_COMPUTE_CYCLES

    del mem_buf
    gc.collect()

    timing['read_time'] = fetch_time - start_time
    timing['average_copy_time'] = copy_avg
    timing['average_calc_time'] = calc_avg
    timing['total_time'] = end_time - fetch_time

    q.put(results_buf)
    q.put(timing)

    return


# run_test(mmap: bool)
#   mmap -          if true, use memory mapping to save files to disk
#                   else, save to disk and load entire files into memory
#   test_data -     contents of file to write
#   test_iter -     how many test cycles to run
#
#   results -       list of length test_iter with memory usage
def run_test(mmap, test_iter, filepath):
    for i in range(test_iter):
        print("Starting iteration {}".format(i))

        q = Queue()

        start_time = time.time()
        worker_proc = Process(target=read_into_buffer, args=(mmap, filepath, q))
        worker_proc.start()

        worker_proc.join()
        end_time = time.time()

        if mmap:
            mmap_basic.append(q.get())
            mmap_compute.extend(q.get())
            mmap_timing.append(q.get())
        else:
            control_basic.append(q.get())
            control_compute.extend(q.get())
            control_timing.append(q.get())

# print the memory usage averages and save boxplot to files
def print_results(target_dir, filepath):
    # print table and generate graph with results of memory mapping the
    #   files and not, in terms of memory pressure

    print("\nSaving Results\n--------------")
    results = [control_basic, mmap_basic, control_compute, mmap_compute]

    # create labels
    labels = ['control_basic', 'mmap_basic', 'control_compute', 'mmap_compute']

    # create basic figure
    fig = matplotlib.pyplot.figure()
    plot = fig.add_subplot(111)

    # plot the box plot
    bp = plot.boxplot(results, labels=labels, showmeans=True)
    plot.set_ylabel('Memory Usage (GB)')

    result_filename = os.path.join(target_dir, filepath)
    matplotlib.pyplot.savefig(result_filename)

    print("Results saved to {}\n".format(result_filename))

    for i, l in enumerate(results):
        print("{:10s}: {:.2f} GB".format(labels[i], sum(l)/len(l)))

# print the timing benchmarks
def print_timing(test_iter):
    print("\nTiming Summary")
    print("--------------\n")

    control = { 'read_time': 0, 'average_copy_time': 0, 'average_calc_time': 0, 'total_time': 0 }
    mmap = { 'read_time': 0, 'average_copy_time': 0, 'average_calc_time': 0, 'total_time': 0 }

    for i in range(test_iter):
        control_iter = control_timing[i]
        for k in control_iter:
            control[k] += control_iter[k]

    for k in control:
        control[k] /= test_iter

    for i in range(test_iter):
        mmap_iter = mmap_timing[i]
        for k in mmap_iter:
            mmap[k] += mmap_iter[k]

    for k in mmap:
        mmap[k] /= test_iter

    print("  Timing   |  Control  |  MMap  ")
    print("-----------|-----------|--------------")
    print(" read time | {:.5f}  |  {:.5f}     ".format(control['read_time'], mmap['read_time']))
    print(" copy time | {:.5f}  |  {:.5f}     ".format(control['average_copy_time'], mmap['average_copy_time']))
    print("  compute  | {:.5f}  |  {:.5f}     ".format(control['average_calc_time'], mmap['average_calc_time']))
    print("   total   | {:.5f}  |  {:.5f}     ".format(control['total_time'], mmap['total_time']))


def main(args):
    target_dir = args.target_dir

    test_iter = args.test_iter

    ### Start the test
    print("\nStarting MMap stress test")

    ### Read random parts of the test data file with and without MMap
    for i, filepath in enumerate(Sources):
        print("\nStarting random file read control test from {}".format(filepath))
        run_test(False, test_iter, filepath)

        print("\nStarting random file read mmap test from {}".format(filepath))
        run_test(True, test_iter, filepath)

        ### Results
        print_results(target_dir, Results[i])

        ### Timing Summary
        print_timing(test_iter)

        control_basic = []
        mmap_basic = []
        control_compute = []
        mmap_compute = []

        control_timing = []
        mmap_timing = []

    print("\nFinished MMap stress test\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Start MMap stress test")

    # required arguments
    parser.add_argument(
        "--target_dir", type=str, required=True, help="Path to directory to save files to"
    )

    # optional arguments
    parser.add_argument(
        "--test_iter", type=int, required=False, default=1, help="Number of test cycles"
    )

    args = parser.parse_args()
    main(args)