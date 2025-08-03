module SolSolver

function find_moves(grid::Matrix{Int64})
    (rows, cols) = size(grid)
    results = []
    for r in 1:rows, c in 1:cols
        if (grid[r, c] == 1)
            if (r-2 > 0) && (grid[r-1, c] == 1) && (grid[r-2, c] == 0)
                new_grid = copy(grid)
                new_grid[r,c] = 0
                new_grid[r-1, c] = 0
                new_grid[r-2, c] = 1
                push!(results, new_grid)
            end
            if (c+2 <= cols) && (grid[r, c+1] == 1) && (grid[r, c+2] == 0)
                new_grid = copy(grid)
                new_grid[r,c] = 0
                new_grid[r, c+1] = 0
                new_grid[r, c+2] = 1
                push!(results, new_grid)
            end
            if (r+2 <= rows) && (grid[r+1, c] == 1) && (grid[r+2, c] == 0)
                new_grid = copy(grid)
                new_grid[r,c] = 0
                new_grid[r+1, c] = 0
                new_grid[r+2, c] = 1
                push!(results, new_grid)
            end
            if (c-2 > 0) && (grid[r, c-1] == 1) && (grid[r, c-2] == 0)
                new_grid = copy(grid)
                new_grid[r,c] = 0
                new_grid[r, c-1] = 0
                new_grid[r, c-2] = 1
                push!(results, new_grid)
            end
        end
    end
    return results
end

function check_similar(board::Matrix{Int64}, boards_seen::Set{Any})
    board in boards_seen ||
    rotl90(board) in boards_seen || 
    rotr90(board) in boards_seen ||
    rot180(board) in boards_seen || 
    transpose(board) in boards_seen ||
    rotl90(transpose(board)) in boards_seen ||
    rotr90(transpose(board)) in boards_seen ||
    rot180(transpose(board)) in boards_seen
end

function solve(board::Matrix{Int64})
    # print(board)
    full_history = []
    boards_seen = Set()
    moves = 0
    function depth_first(history::AbstractVector, nmarbles::Integer)
        for new_grid in find_moves(history[end])
            moves += 1
            if sum(new_grid .== 1) == nmarbles
                push!(history, new_grid)
                full_history = history
                return true
            elseif check_similar(new_grid, boards_seen) # seen a similar board, go to next one
                 continue
            end
            history_copy = copy(history)
            push!(history_copy, new_grid) # Keep track of where we are
            push!(boards_seen, new_grid) # Add the new board to previously seen boards
            if depth_first(history_copy, nmarbles)
                return true
            end
        end
        return false
    end
    for npegs in 1:20
        full_history = []
        boards_seen = Set()
        moves = 0
        sol = depth_first([board], npegs)
        if sol
            println("Best solution: $npegs pegs. No. of moves made to find this: $moves")
            return full_history
        end
    end
    return []
end

export solve

end # module SolSolver
