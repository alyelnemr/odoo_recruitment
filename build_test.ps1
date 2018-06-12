# "C:\PROGRA~2\ODOO11~1.0\nssm\win64\nssm.exe"
$FilePath = "C:\PROGRA~2\ODOO11~1.0\nssm\win64\nssm.exe"
$ArgumentList = "set odoo-server-11.0 AppParameters `"aaaa`""
  
  $OFS = " "
  $process = New-Object System.Diagnostics.Process
  $process.StartInfo.FileName = $FilePath
  $process.StartInfo.Arguments = $ArgumentList
  $process.StartInfo.UseShellExecute = $false
  $process.StartInfo.RedirectStandardOutput = $true
  if ( $process.Start() ) {
    $output = $process.StandardOutput.ReadToEnd() `
      -replace "\r\n$",""
    if ( $output ) {
      if ( $output.Contains("`r`n") ) {
        $output -split "`r`n"
      }
      elseif ( $output.Contains("`n") ) {
        $output -split "`n"
      }
      else {
        $output
      }
    }
    #$process.WaitForExit(5000)
    Stop-Process -name "nssm" -Force
    #& "$Env:SystemRoot\system32\cmd.exe" /c exit $process.ExitCode
  }
