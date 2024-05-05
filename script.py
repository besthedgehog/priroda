import os
import sys
import subprocess
import argparse

# Переменные, которые потом будем задавать через argparse

# to get a name of the json file using terminal
parser = argparse.ArgumentParser()
parser.add_argument(
    '--inputfile',
    help='Название передаваемого выходного файла гессиана',
    required=True,
    dest='inputfile',
    metavar='HESS_TS1.out'
)

parser.add_argument(
    '--charge',
    help='Заряд соединения',
    required=True,
    dest='charge',
    metavar=1
)

parser.add_argument(
    '--mult',
    help='Мультиплётность',
    required=True,
    dest='mult',
    metavar=0
)

parser.add_argument(
    '--steps',
    help='Число шагов для оптимизации',
    required=True,
    dest='steps',
    metavar=10,
    type=int
)

parser.add_argument(
    '--basis',
    help='Базис для расчётов',
    required=True,
    dest='basis',
    metavar='basis4.in',
    type=str
)

parser.add_argument(
    '--follow',
    help='По какой частоте оптимизировать',
    required=True,
    dest='follow',
    metavar=1
)

parser.add_argument(
    '--priroda',
    help='Название природы на компьютере (p, p1, p6 и тд)',
    required=True,
    dest='priroda',
    metavar='p'
)

#Дополнительные
parser.add_argument(
    '--theory',
    help='Используемый метод',
    required=False,
    default='DFT',
    dest='theory',
    metavar='DFT'
)

parser.add_argument(
    '--increasesteps',
    help='Увеличивать число шагов оптимизации с каждой итерации на N шагов',
    required=False,
    default=10,
    dest='increasesteps',
    metavar=10,
    type=int
)

parser.add_argument('--mpirun', help='Использовать распараллеливание вычислений на N ядрах' ,type=int, default=0, dest='mpirun', metavar=8)

parser.add_argument('--four', default=1, dest='four', metavar=1)
parser.add_argument('--acc', type=str, default='1e-8', dest='acc', metavar='1e-8')
parser.add_argument('--conv', type=str, default='1e-6', dest='conv', metavar='1e-6')
parser.add_argument('--iter', default=10, dest='iter', metavar=10)
parser.add_argument('--tolerance', type=str, default='1e-5', dest='tolerance', metavar='1e-5')
parser.add_argument('--trust', type=str, default='0.01', dest='trust', metavar='0.01')
parser.add_argument('--set', type=str, default='L1', dest='set', metavar='L1')





args = parser.parse_args()


# Обязательные
name_of_input_file = args.inputfile #Название файла ГЕССИАНА!
charge=args.charge
mult=args.mult
steps=args.steps

basis=args.basis
follow = args.follow #Мнимая частота, которую мы оптимизируем
name_of_pririda = args.priroda

# Дополнительные
increase_number_of_steps = args.increasesteps #Каждую итерацию прибавлять по N шагов

theory=args.theory

four = args.four
acc = args.acc
conv = args.conv
iter = args.iter
tolerance = args.tolerance
trust = args.trust
set = args.set
mpirun = args.mpirun


current_name_of_IN_file = ''
current_name_of_OUT_file = ''

iteration_number = 0


def run_command(command: str, return_result = False) -> str:
    '''
    Функция запускает bash команду


    По умолчанию возвращается значение result.stdout. 
    Если значение аргумента return_result = True, то будет возвращено 
    значение result
    '''

    print(command)

    result = subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    if result.returncode != 0:
        print(f'Error in the command\n {command}')
        print(result.stderr)
        print(result.stdout)
        sys.exit(result.returncode)
    
    if return_result == True: 
        return result
    else: 
        return result.stdout

def create_command(name_of_in_file) -> str:
    '''
    Функция задаёт команду исходя
    из имени входного файла, параметра mpirun,
    названия файла природы
    -------------------------------------------
    './p input_name.in output_name.out'
    'mpirun -np 8 ./p input_name.in output_name.out'
    '''
    global current_name_of_OUT_file

    result_command = f''
    if mpirun != 0:
        result_command += f'mpirun -np {mpirun} '
    path_to_priroda = os.path.join('.', name_of_pririda)
    result_command += f'{path_to_priroda} '

    current_name_of_OUT_file = name_of_in_file.replace('.in', '.out')
    result_command += f'{name_of_in_file} {current_name_of_OUT_file}'


    return result_command

def create_optim(name_of_out_hess_file):
    '''
    Function creates a hessian from the optimization file
    '''


    #All the information that we should write in (almost) all optimization files
    head_of_optimization_file = ['$system memory=1024 disk=256 path=. $end', 
                                 '$control ', 
                                 ' task=optimize  ', 
                                 f' theory={theory} four={four}', 
                                 f' basis={basis} $end', 
                                 f'$grid acc={acc} $end', 
                                 f'$scf conv={conv} proc=BFGS iter={iter} $end', 
                                 f'$optimize saddle=1 follow={follow} tolerance={tolerance} trust={trust} steps={steps} $end', 
                                 '$molecule ', f' charge={charge} ', f' mult={mult}', 
                                 ' cartesian', f' set={set} ', '$end', 
                                 '$Energy', '$end']
    
    #We need to take the coordinates and the energies out of the hess-file

    
    #pth: the directory where we run code
    with open(name_of_out_hess_file, 'r') as f:
        content = [i.replace('\n', '').replace('eng>', ' ') for i in f.readlines()]
    
    index_of_start_coordinates = 0
    index_of_end_coordinates = 0
    index_of_start_energy = 0
    index_of_end_energy = 0

    for i in range(len(content)):

        if content[i] == ' Atomic Coordinates:':
            index_of_start_coordinates = i
            continue

        if content[i] == ' #':
            index_of_end_coordinates = i
            continue

        if content[i] == ' $Energy': 
            index_of_start_energy = i
            continue

        if content[i] == ' $end':
            index_of_end_energy = i
            break
    

                      #head of file                                              #coordinates                                  #$end $Energy                           #Energy                                         #$end
    write_into_file = head_of_optimization_file[:13] + content[index_of_start_coordinates+1:index_of_end_coordinates] + head_of_optimization_file[13:15] + content[index_of_start_energy+1:index_of_end_energy] + head_of_optimization_file[15:]

    final_text = '\n'.join(write_into_file)

    #Name of the out file  
    # in the format: optim_name.in
    name_of_final_in_file = f'optim_{iteration_number}_' + name_of_out_hess_file.replace('.out', '.in')

    with open(name_of_final_in_file, 'w') as f:
        f.write(final_text)

    print('Name of our input optimization file')
    print(name_of_final_in_file)

    return name_of_final_in_file


def create_hess(name_of_out_optimization_file):
    '''
    Function creates hessian from an optimization file
    Parameters
    ----------
    name_of_out_optimization_file : string
    The name of the optimization file, where the coordinates and the energies come from.
    '''

    #All the information that we should write in (almost) all optimization files
    head_of_hess_file = ['$system memory=1024 disk=256 path=. $end', 
            f'$control task=hessian theory={theory} four={four} basis={basis} $end', 
            f'$scf conv={conv} proc=BFGS iter={iter} $end', f'$grid acc={acc} $end', 
            '$end', f'$molecule charge={charge} mult={mult} cartesian set={set}', '$end', 
            '$integral ', 'direct=1 ', '$end']
    

    #We need to take the atomic coordinates out of the optimization file
    #pth: the directory where we run code
    with open(name_of_out_optimization_file, 'r') as f:
        content = [i.replace('\n', '').replace('eng>', ' ') for i in f.readlines()]
    
    index_of_end_of_coordinates = 0
    index_of_beginning_of_coordinates = 0

    #Read the optim-file from the end, 
    # because we need the last step of the optimization
    for i in range(len(content)-1, -1, -1):
        if content[i] == ' #': #the end of the coordinates 
            index_of_end_of_coordinates = i
            continue
        if content[i] == ' Atomic Coordinates:':
            index_of_beginning_of_coordinates = i
            break
    
    write_into_file = head_of_hess_file[:6] + content[index_of_beginning_of_coordinates+1:index_of_end_of_coordinates] + head_of_hess_file[6:]
    final_text = '\n'.join(write_into_file)

    name_of_hess_in_file = f'HESS_{iteration_number}_' + name_of_out_optimization_file.replace('.out', '.in')

    with open(name_of_hess_in_file, 'w') as f:
        f.write(final_text)

    print('Name of our input hessian file')
    print(name_of_hess_in_file)

    return name_of_hess_in_file




def main():
    '''
    Главная функция, которая запускает файл
    '''
    #create_optim('3TS13_mult3_hess_1.out')
    #create_hess('3TS13_mult3_1_steps1_10.out')
    global steps
    global iteration_number

    current_name_of_OUT_file =  name_of_input_file




    # Мы в ручном режиме посчитали гессиан и выбрали частоту
    # Начинаем с создания и запуска файла оптимизации

    while True:
        iteration_number += 1

        steps += increase_number_of_steps

        # Создадим файл оптимизации
        current_name_of_IN_file = create_optim(current_name_of_OUT_file)

        # Запустим оптимизацию
        run_command(create_command(current_name_of_IN_file))

        # В функции create_command произошло неявное обновление 
        # переменной current_name_of_OUT_file

        with open(current_name_of_OUT_file) as f:
            current_content = f.read()
        
        if 'SCF is far from convergence' in current_content:
            print('SCF is far from convergence')
            sys.exit(1)
        
        if 'OPTIMIZATION CONVERGED' in current_content:
            print('OPTIMIZATION CONVERGED')
            # Создадим файл гессиана
            current_name_of_IN_file = create_hess(current_name_of_OUT_file)
            run_command(create_command(current_name_of_IN_file))
            print('FINAL!')
            print(f'Final hessian {current_name_of_OUT_file}')
            sys.exit(0)

        # Продолжаем цикл
        current_name_of_IN_file = create_hess(current_name_of_OUT_file)
        run_command(create_command(current_name_of_IN_file))
        



if __name__ == '__main__':
    main()