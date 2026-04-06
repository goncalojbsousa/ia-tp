param(
    [string]$Agent = 'group07',
    [int]$Reps = 5,
    [string[]]$Mazes = @(),
    [int]$DefaultMaxTurns = 250,
    [switch]$IncludeGroupAgents,
    [switch]$Json
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path 'run.py')) {
    throw 'Run this script from the project root (folder containing run.py).'
}

if (-not $Mazes -or $Mazes.Count -eq 0) {
    $Mazes = Get-ChildItem .\mazes\*.txt |
        Sort-Object Name |
        ForEach-Object { "mazes/$($_.Name)" }

    if (-not $Mazes -or $Mazes.Count -eq 0) {
        throw 'No maze files found in mazes/.'
    }
}

$turnsByMaze = @{
    'mazes/maze01.txt' = 200
    'mazes/maze02.txt' = 250
    'mazes/maze03.txt' = 300
}

foreach ($maze in $Mazes) {
    if (-not (Test-Path $maze)) {
        throw "Maze file not found: $maze"
    }
}

if (-not (Test-Path (Join-Path 'agents' ($Agent + '.py')))) {
    throw "Agent file not found: agents/$Agent.py"
}

$refAgents = Get-ChildItem .\agents\*_agent.py |
    ForEach-Object { $_.BaseName -replace '_agent$', '' }

$groupAgents = @()
if ($IncludeGroupAgents) {
    $groupAgents = Get-ChildItem .\agents\group*.py |
        ForEach-Object { $_.BaseName } |
        Where-Object { $_ -ne $Agent -and $_ -ne 'group99' }
}

$opponents = ($refAgents + $groupAgents) | Sort-Object -Unique
if (-not $opponents -or $opponents.Count -eq 0) {
    throw 'No opponents found in agents/.'
}

$results = @()

function Count-ByOutcome {
    param(
        [array]$Rows,
        [string]$Tag
    )

    return @($Rows | Where-Object Outcome -eq $Tag).Count
}

foreach ($maze in $Mazes) {
    $maxTurns = if ($turnsByMaze.ContainsKey($maze)) { $turnsByMaze[$maze] } else { $DefaultMaxTurns }

    foreach ($opp in $opponents) {
        $skipOpponent = $false
        foreach ($order in @('group-first', 'group-second')) {
            if ($skipOpponent) { break }
            for ($i = 1; $i -le $Reps; $i++) {
                if ($order -eq 'group-first') {
                    $a1 = $Agent
                    $a2 = $opp
                }
                else {
                    $a1 = $opp
                    $a2 = $Agent
                }

                Write-Host "Running: py run.py $maze $maxTurns $a1 $a2"
                $output = (Invoke-Expression "py run.py $maze $maxTurns $a1 $a2") | Out-String

                if ($output -match 'could not be loaded\.' -or $output -match 'could not find .* in ''agents/'' folder\.') {
                    Write-Warning "Skipping opponent '$opp' on maze '$maze': agent could not be loaded."
                    $skipOpponent = $true
                    break
                }

                # Support both output formats:
                # - "Agent 1 (name): 12"
                # - "Agent 1 - name : 12 pts"
                $score1Match = [regex]::Match($output, 'Agent 1(?:\s*-\s*[^\r\n:]+|\s*\([^\)]+\))\s*:\s+(\d+)')
                $score2Match = [regex]::Match($output, 'Agent 2(?:\s*-\s*[^\r\n:]+|\s*\([^\)]+\))\s*:\s+(\d+)')
                if (-not $score1Match.Success -or -not $score2Match.Success) {
                    throw "Could not parse scores from output.`n$output"
                }

                $s1 = [int]$score1Match.Groups[1].Value
                $s2 = [int]$score2Match.Groups[1].Value
                $winner = [regex]::Match($output, 'Winner(?: by points)?: Agent ([12])').Groups[1].Value
                $isDraw = $output -match 'Result(?: by points)?: Draw'

                if ($order -eq 'group-first') {
                    $groupScore = $s1
                    $oppScore = $s2
                    if ($winner -eq '1') { $outcome = 'W' }
                    elseif ($winner -eq '2') { $outcome = 'L' }
                    elseif ($isDraw) { $outcome = 'D' }
                    else { $outcome = '?' }
                }
                else {
                    $groupScore = $s2
                    $oppScore = $s1
                    if ($winner -eq '2') { $outcome = 'W' }
                    elseif ($winner -eq '1') { $outcome = 'L' }
                    elseif ($isDraw) { $outcome = 'D' }
                    else { $outcome = '?' }
                }

                $results += [pscustomobject]@{
                    Maze = $maze
                    Opponent = $opp
                    Order = $order
                    Rep = $i
                    GroupScore = $groupScore
                    OppScore = $oppScore
                    Diff = $groupScore - $oppScore
                    Outcome = $outcome
                }
            }
        }
    }
}

if ($results.Count -eq 0) {
    throw 'No valid benchmark results were produced. Check agent names and loading errors.'
}

$summary = $results |
    Group-Object Maze, Opponent |
    ForEach-Object {
        $rows = $_.Group
        [pscustomobject]@{
            Maze = $rows[0].Maze
            Opponent = $rows[0].Opponent
            Games = $rows.Count
            Wins = Count-ByOutcome -Rows $rows -Tag 'W'
            Draws = Count-ByOutcome -Rows $rows -Tag 'D'
            Losses = Count-ByOutcome -Rows $rows -Tag 'L'
            AvgGroup = [math]::Round((($rows | Measure-Object GroupScore -Average).Average), 2)
            AvgOpp = [math]::Round((($rows | Measure-Object OppScore -Average).Average), 2)
            AvgDiff = [math]::Round((($rows | Measure-Object Diff -Average).Average), 2)
        }
    } |
    Sort-Object Maze, Opponent

$total = [pscustomobject]@{
    Maze = 'ALL'
    Opponent = 'all-selected'
    Games = $results.Count
    Wins = Count-ByOutcome -Rows $results -Tag 'W'
    Draws = Count-ByOutcome -Rows $results -Tag 'D'
    Losses = Count-ByOutcome -Rows $results -Tag 'L'
    AvgGroup = [math]::Round((($results | Measure-Object GroupScore -Average).Average), 2)
    AvgOpp = [math]::Round((($results | Measure-Object OppScore -Average).Average), 2)
    AvgDiff = [math]::Round((($results | Measure-Object Diff -Average).Average), 2)
}

if ($Json) {
    ($summary + $total) | ConvertTo-Json -Depth 5
}
else {
    ''
    '=== SUMMARY ==='
    $summary | Format-Table -AutoSize | Out-String

    '=== TOTAL ==='
    $total | Format-List | Out-String
}
