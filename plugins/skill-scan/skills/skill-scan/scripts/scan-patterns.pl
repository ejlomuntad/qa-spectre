#!/usr/bin/env perl
# skill-scan pattern pass (Step 3). Read only: it never runs anything from the target.
#
#   perl scan-patterns.pl <target> [<target> ...]   one JSON object per match, on stdout
#   perl scan-patterns.pl --list-changed <base>     skill/plugin folders changed since <base>, one per line
#
# The patterns come from ../references/patterns.md (rows of the P1-P8 tables), so edit them
# there. Rows whose cell is a command (P7.x, P8.3) are implemented natively below.

use strict;
use warnings;
use FindBin;
use File::Find;
use File::Spec;
use Encode qw(decode);

binmode STDOUT, ':encoding(UTF-8)';

if (@ARGV && $ARGV[0] eq '--list-changed') {
    list_changed($ARGV[1] // 'origin/main');
    exit 0;
}
die "usage: $0 <target> [<target> ...] | --list-changed <base>\n" unless @ARGV;

my $patterns_md = "$FindBin::Bin/../references/patterns.md";
my (@line_rules, @mcp_rules, %ci);

open my $pf, '<:encoding(UTF-8)', $patterns_md or die "can't read $patterns_md: $!\n";
while (my $row = <$pf>) {
    # Patterns can contain a literal [|], so anchor on the last two columns
    # ("Looks for" never contains a pipe) instead of splitting on |.
    next unless $row =~ /^\| P\d/;
    # A row that looks like a rule but doesn't parse would silently switch that check off: stop instead.
    die "patterns.md: can't parse rule row: $row" unless $row =~ /^\| (P\d\.\d+) \| (.+) \| ([^|]*) \| (block|candidate) \|\s*$/;
    my ($id, $cell, $looks) = ($1, $2, $3);
    $ci{$id} = $4;
    next if $id =~ /^P7\./ || $id eq 'P8.3';    # command rows: native checks below
    next unless $cell =~ /^`(.*)`$/;
    (my $pat = $1) =~ s/\\\|/|/g;
    my $re = ($looks // '') =~ /case-sensitive/ ? qr/$pat/ : qr/$pat/i;
    push @{ $id =~ /^P8\./ ? \@mcp_rules : \@line_rules }, [ $id, $re ];
}
close $pf;

my %binary_ext = map { $_ => 1 } qw(zip tar gz tgz exe dylib so bin pyc wasm);

for my $target (@ARGV) {
    die "not found: $target\n" unless -e $target;
    my @files;
    if (-d $target) {
        find({ no_chdir => 1, wanted => sub {
            if (-l $_) { emit('P7.6', $_, 0, 'symlink -> ' . (readlink($_) // '?')); return }
            if (-d $_ && /\/\.git$/) { $File::Find::prune = 1; return }
            if (-d $_ && /\/node_modules$/) {    # vendored code: too big to read, so the gate must see it
                emit('P7.6', $_, 0, 'vendored node_modules folder, not scanned');
                $File::Find::prune = 1;
                return;
            }
            push @files, $_ if -f $_;
        } }, $target);
    } elsif (-l $target) {    # a single file that is a symlink (e.g. CLAUDE.md -> elsewhere): never read it
        emit('P7.6', $target, 0, 'symlink -> ' . (readlink($target) // '?'));
    } else {
        @files = ($target);
    }
    scan_file($_) for sort @files;
}

sub scan_file {
    my ($file) = @_;
    (my $ext = lc $file) =~ s/.*\.//;
    if ($binary_ext{$ext} || $file =~ /\.tar\./) {
        emit('P7.6', $file, 0, 'binary or archive');
        return;
    }
    if (-s $file && -B $file) {    # can't grep it, so the gate must see it (empty files aren't binary)
        emit('P7.6', $file, 0, 'binary file, not scanned');
        return;
    }
    my $is_mcp = $file =~ /(^|\/)(\.mcp\.json|plugin\.json|settings[^\/]*\.json)$/;

    open my $fh, '<:raw', $file or return;
    my $n = 0;
    while (my $raw = <$fh>) {
        $n++;
        my $line = decode('UTF-8', $raw);
        $line =~ s/\r?\n$//;
        for my $r (@line_rules) {
            emit($r->[0], $file, $n, $line) if $line =~ $r->[1];
        }
        if ($is_mcp) {
            for my $r (@mcp_rules) {
                emit($r->[0], $file, $n, $line) if $line =~ $r->[1];
            }
            emit('P8.3', $file, $n, $line) if $line =~ /"description"\s*:/ && length $line > 300;
        }
        emit('P7.1', $file, $n, $line) if $line =~ /[A-Za-z0-9+\/]{120,}={0,2}/;
        emit('P7.2', $file, $n, $line) if $line =~ /(\\x[0-9a-fA-F]{2}){8,}|(\\u[0-9a-fA-F]{4}){6,}/;
        emit('P7.3', $file, $n, 'zero-width/bidi character')
            if $line =~ /[\x{200B}\x{200C}\x{200D}\x{2060}\x{FEFF}\x{202A}-\x{202E}\x{2066}-\x{2069}]/;
        emit('P7.4', $file, $n, 'unicode tag characters') if $line =~ /[\x{E0000}-\x{E007F}]/;
        emit('P7.5', $file, $n, length($line) . ' chars') if length $line > 2000;
    }
    close $fh;
}

sub emit {
    my ($id, $file, $line, $text) = @_;
    # Never print a full secret: keep the first 4 characters of each match.
    $text =~ s/(?<![A-Za-z0-9])(sk-ant-|sk_live_|sk_test_|sk-|ghp_|gho_|ghs_|ghu_|ghr_|github_pat_|glpat-|xox[baprs]-|npm_|AIza|AKIA)([A-Za-z0-9_\-]{4})[A-Za-z0-9_\-]+/$1$2****/g;
    $text =~ s/\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]+/eyJ****.****.****/g;    # JWTs
    $text =~ s/^\s+//;
    $text = substr($text, 0, 200) . '…' if length $text > 200;
    printf "{\"id\":%s,\"ci\":%s,\"file\":%s,\"line\":%d,\"text\":%s}\n",
        map({ json_str($_) } $id, $ci{$id} // 'candidate', $file), $line, json_str($text);
}

sub json_str {
    my ($s) = @_;
    $s =~ s/(["\\])/\\$1/g;
    $s =~ s/\n/\\n/g;
    $s =~ s/\t/\\t/g;
    $s =~ s/([\x00-\x1f\x{2028}\x{2029}])/sprintf('\\u%04x', ord $1)/ge;
    return "\"$s\"";
}

# Map each changed file to its nearest folder with a SKILL.md or .claude-plugin/,
# keep standalone MCP and settings files, then drop targets inside other targets.
sub list_changed {
    my ($base) = @_;
    die "invalid base ref: $base\n" unless $base =~ m{^[\w./-]+$} && $base !~ /^-/;
    # List form (no shell) and NUL-separated output, so odd file names can't break out or get lost.
    # Deletions (D) and type changes (T, e.g. a file swapped for a symlink) count too: a PR could
    # otherwise remove a safety rule or swap in a symlink and pass with "nothing changed".
    open my $git, '-|', 'git', '-c', 'core.quotePath=false', 'diff', '-z', '--name-status', '--no-renames',
        '--diff-filter=ACMRTD', "$base...HEAD" or die "can't run git: $!\n";
    my @fields = do { local $/; split /\0/, (<$git> // '') };
    close $git or die "git diff against $base failed\n";
    my %targets;
    while (@fields) {
        my ($status, $p) = splice @fields, 0, 2;
        last unless defined $p;
        die "changed path contains a line break: refusing to continue\n" if $p =~ /[\r\n]/;
        my $gone = $status eq 'D';
        die "changed path not found: $p\n" unless $gone || -e $p || -l $p;
        # Instruction and config files that affect Claude even outside a skill folder.
        if (!$gone && $p =~ /(^|\/)(\.mcp\.json|settings[^\/]*\.json|CLAUDE\.md|AGENTS\.md)$/) { $targets{$p} = 1; next }
        my @parts = File::Spec->splitdir($p);
        pop @parts;
        my $found = 0;
        while (@parts) {    # nearest skill or plugin folder (for a deleted file: the folder it was in)
            my $dir = File::Spec->catdir(@parts);
            if (-f "$dir/SKILL.md" || -f "$dir/skill.md" || -d "$dir/.claude-plugin") {
                $targets{$dir} = 1;
                $found = 1;
                last;
            }
            pop @parts;
        }
        next if $found;
        # Anything else under .claude/ (hooks, agents, commands, rules): scan its first-level folder.
        if ($p =~ m{^\.claude/([^/]+)}) {
            my $dir = ".claude/$1";
            $targets{$dir} = 1 if -d $dir || (-e $dir && !$gone);
        }
    }
    my @all = sort keys %targets;
    for my $t (@all) {
        print "$t\n" unless grep { $_ ne $t && index($t, "$_/") == 0 } @all;
    }
}
