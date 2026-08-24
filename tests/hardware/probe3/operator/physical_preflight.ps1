[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

function Read-CimSafe {
    param([string]$ClassName)
    try { @(Get-CimInstance -ClassName $ClassName -ErrorAction Stop) }
    catch { @([pscustomobject]@{ inventory_error = $_.Exception.Message }) }
}

$disks = @(try {
    Get-Disk -ErrorAction Stop | ForEach-Object {
        [pscustomobject]@{
            number = $_.Number; friendly_name = $_.FriendlyName
            serial_number = $_.SerialNumber; bus_type = [string]$_.BusType
            partition_style = [string]$_.PartitionStyle; size = $_.Size
            is_boot = $_.IsBoot; is_system = $_.IsSystem
            is_offline = $_.IsOffline; is_read_only = $_.IsReadOnly
        }
    }
} catch { [pscustomobject]@{ inventory_error = $_.Exception.Message } })

$volumes = @(try {
    Get-Volume -ErrorAction Stop | ForEach-Object {
        [pscustomobject]@{
            drive_letter = [string]$_.DriveLetter; label = $_.FileSystemLabel
            file_system = $_.FileSystem; drive_type = [string]$_.DriveType
            size = $_.Size; size_remaining = $_.SizeRemaining
            health_status = [string]$_.HealthStatus
        }
    }
} catch { [pscustomobject]@{ inventory_error = $_.Exception.Message } })

$serial = @(Read-CimSafe 'Win32_SerialPort' | ForEach-Object {
    if ($_.inventory_error) { $_ } else {
        [pscustomobject]@{ device_id = $_.DeviceID; name = $_.Name; pnp_id = $_.PNPDeviceID }
    }
})

$capture = @(Read-CimSafe 'Win32_PnPEntity' | Where-Object {
    $_.inventory_error -or $_.PNPClass -in @('Camera', 'Image') -or
    $_.Name -match '(?i)capture|camera|webcam|usb video'
} | ForEach-Object {
    if ($_.inventory_error) { $_ } else {
        [pscustomobject]@{ name = $_.Name; pnp_class = $_.PNPClass; status = $_.Status; pnp_id = $_.PNPDeviceID }
    }
})

$toolNames = @('cdrecord', 'wodim', 'imgburn', 'fenrir-loader', 'satiator-menu',
    'mode-ode', 'pseudo-saturn', 'iso2raw')
$loaderTools = @($toolNames | ForEach-Object {
    Get-Command $_ -ErrorAction SilentlyContinue | ForEach-Object {
        [pscustomobject]@{ requested_name = $_.Name; path = $_.Source; version = [string]$_.Version }
    }
})

[pscustomobject]@{
    schema = 'avsp-hw01-read-only-preflight-v1'
    captured_utc = (Get-Date).ToUniversalTime().ToString('o')
    computer = $env:COMPUTERNAME
    write_performed = $false
    authorization_granted = $false
    warning = 'Inventory only. No target write is authorized or performed.'
    disks = $disks
    volumes = $volumes
    serial_debug_devices = $serial
    capture_devices = $capture
    loader_tools_on_path = $loaderTools
} | ConvertTo-Json -Depth 6
