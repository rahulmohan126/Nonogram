import pulp

def solve(SIZE, s_r, s_c):

    M = SIZE  # ROWS
    N = SIZE  # COLUMNS

    k_r = [len(x) for x in s_r]
    k_c = [len(x) for x in s_c]

    e_r = []
    l_r = []

    for row in s_r:
        earliest = []
        running_sum = 0
        for cluster in row:
            earliest.append(running_sum)
            running_sum += cluster + 1

        latest = []
        running_sum = N
        for cluster in row[::-1]:
            latest.append(running_sum - cluster)
            running_sum -= cluster + 1

        e_r.append(earliest)
        l_r.append(latest[::-1])

    e_c = []
    l_c = []

    for column in s_c:
        earliest = []
        running_sum = 0
        for cluster in column:
            earliest.append(running_sum)
            running_sum += cluster + 1

        latest = []
        running_sum = N
        for cluster in column[::-1]:
            latest.append(running_sum - cluster)
            running_sum -= cluster + 1

        e_c.append(earliest)
        l_c.append(latest[::-1])

    model = pulp.LpProblem("Nonogram", pulp.LpMinimize)

    def z_name(i, j):
        return "z_{%d,%d}" % (i, j)


    def y_name(i, t, j):
        return "y_{%d,%d,%d}" % (i, t, j)


    def x_name(j, t, i):
        return "x_{%d,%d,%d}" % (j, t, i)

    # Variables

    z_vars = pulp.LpVariable.dict(
        "%s",
        [z_name(i, j) for i in range(M) for j in range(N)],
        cat=pulp.LpBinary,
    )

    y_vars = pulp.LpVariable.dict(
        "%s",
        [y_name(i, t, j) for i in range(M) for t in range(k_r[i]) for j in range(e_r[i][t], l_r[i][t] + 1)],
        cat=pulp.LpBinary,
    )

    x_vars = pulp.LpVariable.dict(
        "%s",
        [x_name(j, t, i) for j in range(N) for t in range(k_c[j]) for i in range(e_c[j][t], l_c[j][t] + 1)],
        cat=pulp.LpBinary,
    )

    # Constraints

    # Ensure each cluster appears only once in row/column
    for i in range(M):
        for t in range(k_r[i]):
            eq = sum(y_vars[y_name(i,t,j)] for j in range(e_r[i][t], l_r[i][t] + 1)) == 1
            model += eq

    for j in range(N):
        for t in range(k_c[j]):
            eq = sum(x_vars[x_name(j,t,i)] for i in range(e_c[j][t], l_c[j][t] + 1)) == 1
            model += eq


    # Ensure cluster appear one after the other
    for j in range(N):
        for t in range(k_c[j] - 1):
            for i in range(e_c[j][t], l_c[j][t] + 1):
                eq = x_vars[x_name(j,t,i)] <= sum(x_vars[x_name(j,t+1,ip)] for ip in range(i+s_c[j][t]+1, l_c[j][t+1] + 1))
                model += eq

    for i in range(M):
        for t in range(k_r[i] - 1):
            for j in range(e_r[i][t], l_r[i][t] + 1):
                eq = y_vars[y_name(i,t,j)] <= sum(y_vars[y_name(i,t+1,jp)] for jp in range(j+s_r[i][t]+1, l_r[i][t+1] + 1))
                model += eq
    

    # Ensure each square is covered by one of the row's and column's clusters
    for i in range(M):
        for j in range(N):
            eq = 0
            for t in range(k_r[i]):
                for jp in range(j-s_r[i][t]+1, j + 1):
                    if jp >= e_r[i][t] and jp <= l_r[i][t]:
                        eq += y_vars[y_name(i,t,jp)]
            
            model += z_vars[z_name(i, j)] <= eq

            eq = 0
            for t in range(k_c[j]):
                for ip in range(i-s_c[j][t]+1, i + 1):
                    if ip >= e_c[j][t] and ip <= l_c[j][t]:
                        eq += x_vars[x_name(j,t,ip)]
            
            model += z_vars[z_name(i, j)] <= eq


    # Ensure all other squares are blank
    for i in range(M):
        for j in range(N):
            for t in range(k_r[i]):
                for jp in range(j-s_r[i][t]+1, j + 1):
                    if jp >= e_r[i][t] and jp <= l_r[i][t]:
                        model += z_vars[z_name(i, j)] >= y_vars[y_name(i,t,jp)]

    for i in range(M):
        for j in range(N):
            for t in range(k_c[j]):
                for ip in range(i-s_c[j][t]+1, i + 1):
                    if ip >= e_c[j][t] and ip <= l_c[j][t]:
                        model += z_vars[z_name(i, j)] >= x_vars[x_name(j,t,ip)]

    # Solve and output

    res = model.solve(pulp.PULP_CBC_CMD(msg=0)) == pulp.LpStatusOptimal
    print('Nonogram Solved:', res)

    grid = [[False]*N for _ in range(M)]

    for name in z_vars:
        if z_vars[name].value() > 0:
            name = name.replace('z_{', '').replace('}', '')
            i,j = map(int, name.split(','))
            grid[i][j] = True
    return res, grid

if __name__ == "__main__":
    s_r = [[2], [6], [3,2], [2,4], [1,5], [2,5], [3,4], [5,5], [2,4,5], [1,10], [8,2], [4,3], [1,2,3], [2,3], [2,1]]
    s_c = [[1,1,1], [1,1,2], [2,4], [2,4], [2,7,2], [9,2], [2,7], [1,5], [1,3], [2,4], [2,7], [10], [9],[6],[2]]
    SIZE = len(s_r)

    r, g = solve(SIZE, s_r, s_c)

    for line in g:
        for i in line:
            print('X' if i else '-', end='')
        print()