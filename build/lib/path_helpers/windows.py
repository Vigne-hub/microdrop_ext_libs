# -*- coding: utf-8 -*-
from collections import OrderedDict

from pythoncom import com_error
from win32com.shell import shell, shellcon

from . import path


def windows_path(csidl_constant):
    '''
    Resolve [CSIDL][1] constant into file system path.

    Args
    ----

        csidl_constant (int) : [CSIDL][1] folder identify constant.

    Returns
    -------

        (path) : Path corresponding to specified `csidl_constant` value.

    [1]: https://technet.microsoft.com/en-ca/library/cc749104(v=ws.10).aspx
    '''
    return path(shell.SHGetFolderPath(0, csidl_constant, 0, 0))


def resolve_csidl_paths(csidl_constant_names):
    '''
    Args
    ----

        csidl_constants (iterable) : Sequence of CSIDL constant names.
            Unrecognized CSIDL constant names are ignored.

    Returns
    -------

        (OrderedDict) : Resolved Windows file system path for each CSIDL
            constant name.
    '''
    paths = OrderedDict()

    for constant_i in csidl_constant_names:
        if hasattr(shellcon, constant_i):
            try:
                win_path_i = windows_path(getattr(shellcon, constant_i))
                constant_i = (constant_i[len('CSIDL_'):]
                              if constant_i.startswith('CSIDL_') else constant_i)
                paths[constant_i] = win_path_i
            except com_error:
                continue
    return paths


CSIDL_SYSTEM_DESCRIPTIONS = OrderedDict([
    (r'ALLUSERSAPPDATA', r'Same as CSIDL_COMMON_APPDATA.'),
    (r'ALLUSERSPROFILE', r'Refers to %PROFILESFOLDER%\Public or %PROFILESFOLDER%\all users.'),
    (r'COMMONPROGRAMFILES', r'Same as CSIDL_PROGRAM_FILES_COMMON.'),
    (r'COMMONPROGRAMFILES(X86)', r'Refers to the C:\Program Files (x86)\Common Files folder on 64-bit systems.'),
    (r'CSIDL_COMMON_ADMINTOOLS', r'Version 5.0. The file system directory containing administrative tools for all users of the computer.'),
    (r'CSIDL_COMMON_ALTSTARTUP', r'The file system directory that corresponds to the nonlocalized Startup program group for all users.'),
    (r'CSIDL_COMMON_APPDATA', r'Version 5.0. The file system directory containing application data for all users. A typical path is C:\Documents and Settings\All Users\Application Data.'),
    (r'CSIDL_COMMON_DESKTOPDIRECTORY', r'The file system directory that contains files and folders that appear on the desktop for all users. A typical path is C:\Documents and Settings\All Users\Desktop.'),
    (r'CSIDL_COMMON_DOCUMENTS', r'The file system directory that contains documents that are common to all users. A typical path is C:\Documents and Settings\All Users\Documents.'),
    (r'CSIDL_COMMON_FAVORITES', r'The file system directory that serves as a common repository for favorite items common to all users.'),
    (r'CSIDL_COMMON_MUSIC', r'Version 6.0. The file system directory that serves as a repository for music files common to all users. A typical path is C:\Documents and Settings\All Users\Documents\My Music.'),
    (r'CSIDL_COMMON_PICTURES', r'Version 6.0. The file system directory that serves as a repository for image files common to all users. A typical path is C:\Documents and Settings\All Users\Documents\My Pictures.'),
    (r'CSIDL_COMMON_PROGRAMS', r'The file system directory that contains the directories for the common program groups that appear on the Start menu for all users. A typical path is C:\Documents and Settings\All Users\Start Menu\Programs.'),
    (r'CSIDL_COMMON_STARTMENU', r'The file system directory that contains the programs and folders that appear on the Start menu for all users. A typical path is C:\Documents and Settings\All Users\Start Menu.'),
    (r'CSIDL_COMMON_STARTUP', r'The file system directory that contains the programs that appear in the Startup folder for all users. A typical path is C:\Documents and Settings\All Users\Start Menu\Programs\Startup.'),
    (r'CSIDL_COMMON_TEMPLATES', r'The file system directory that contains the templates that are available to all users. A typical path is C:\Documents and Settings\All Users\Templates.'),
    (r'CSIDL_COMMON_VIDEO', r'Version 6.0. The file system directory that serves as a repository for video files common to all users. A typical path is C:\Documents and Settings\All Users\Documents\My Videos.'),
    (r'CSIDL_DEFAULT_APPDATA', r'Refers to the Appdata folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_DEFAULT_LOCAL_APPDATA', r'Refers to the local Appdata folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_DEFAULT_COOKIES', r'Refers to the Cookies folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_DEFAULT_CONTACTS', r'Refers to the Contacts folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_DEFAULT_DESKTOP', r'Refers to the Desktop folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_DEFAULT_DOWNLOADS', r'Refers to the Downloads folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_DEFAULT_FAVORITES', r'Refers to the Favorites folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_DEFAULT_HISTORY', r'Refers to the History folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_DEFAULT_INTERNET_CACHE', r'Refers to the Internet Cache folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_DEFAULT_PERSONAL', r'Refers to the Personal folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_DEFAULT_MYDOCUMENTS', r'Refers to the My Documents folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_DEFAULT_MYPICTURES', r'Refers to the My Pictures folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_DEFAULT_MYMUSIC', r'Refers to the My Music folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_DEFAULT_MYVIDEO', r'Refers to the My Videos folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_DEFAULT_RECENT', r'Refers to the Recent folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_DEFAULT_SENDTO', r'Refers to the Send To folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_DEFAULT_STARTMENU', r'Refers to the Start Menu folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_DEFAULT_PROGRAMS', r'Refers to the Programs folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_DEFAULT_STARTUP', r'Refers to the Startup folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_DEFAULT_TEMPLATES', r'Refers to the Templates folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_DEFAULT_QUICKLAUNCH', r'Refers to the Quick Launch folder inside %DEFAULTUSERPROFILE%.'),
    (r'CSIDL_FONTS', r'A virtual folder containing fonts. A typical path is C:\Windows\Fonts.'),
    (r'CSIDL_PROGRAM_FILESX86', r'The Program Files folder on 64-bit systems. A typical path is C:\Program Files(86).'),
    (r'CSIDL_PROGRAM_FILES_COMMONX86', r'A folder for components that are shared across applications on 64-bit systems. A typical path is C:\Program Files(86)\Common.'),
    (r'CSIDL_PROGRAM_FILES', r'Version 5.0. The Program Files folder. A typical path is C:\Program Files.'),
    (r'CSIDL_PROGRAM_FILES_COMMON', r'Version 5.0. A folder for components that are shared across applications. A typical path is C:\Program Files\Common. Valid only for computers running Windows NT, Windows 2000, and Windows XP. Not valid for Windows Millennium Edition.'),
    (r'CSIDL_RESOURCES', r'For computers running Windows Vista, the file system directory that contains resource data. A typical path is C:\Windows\Resources.'),
    (r'CSIDL_SYSTEM', r'Version 5.0. The Windows System folder. A typical path is C:\Windows\System32.'),
    (r'CSIDL_WINDOWS', r'Version 5.0. The Windows directory or SYSROOT. This corresponds to the %WINDIR% or %SYSTEMROOT% environment variables. A typical path is C:\Windows.'),
    (r'DEFAULTUSERPROFILE', r'Refers to the value in HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList [DefaultUserProfile].'),
    (r'PROFILESFOLDER', r'Refers to the value in HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList [ProfilesDirectory].'),
    (r'PROGRAMFILES', r'Same as CSIDL_PROGRAM_FILES.'),
    (r'PROGRAMFILES(X86)', r'Refers to the C:\Program Files (x86) folder on 64-bit systems.'),
    (r'SYSTEM', r'Refers to %WINDIR%\system32.'),
    (r'SYSTEM16', r'Refers to %WINDIR%\system.'),
    (r'SYSTEM32', r'Refers to %WINDIR%\system32.'),
    (r'SYSTEMPROFILE', r'Refers to the value in HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\ProfileList\\S-1-5-18 [ProfileImagePath].'),
    (r'SYSTEMROOT', r'Refers to the root of the system drive.'),
    (r'WINDIR', r'Refers to the Windows folder located on the system drive.')])

CSIDL_USER_DESCRIPTIONS = OrderedDict([
    (r'APPDATA', r'''Same as CSIDL_APPDATA.'''),
    (r'CSIDL_ADMINTOOLS', r'''The file system directory that is used to store administrative tools for an individual user. The Microsoft Management Console (MMC) will save customized consoles to this directory, and it will roam with the user.'''),
    (r'CSIDL_ALTSTARTUP', r'''The file system directory that corresponds to the user's nonlocalized Startup program group.'''),
    (r'CSIDL_APPDATA', r'''The file system directory that serves as a common repository for application-specific data. A typical path is C:\Documents and Settings\username\Application Data. This CSIDL is supported by the redistributable Shfolder.dll for systems that do not have the Microsoft Internet Explorer 4.0 integrated shell installed.'''),
    (r'CSIDL_BITBUCKET', r'''The virtual folder containing the objects in the user's Recycle Bin.'''),
    (r'CSIDL_CDBURN_AREA', r'''The file system directory acting as a staging area for files waiting to be written to CD. A typical path is C:\Documents and Settings\username\Local Settings\Application Data\Microsoft\CD Burning.'''),
    (r'CSIDL_CONNECTIONS', r'''The virtual folder representing Network Connections, containing network and dial-up connections.'''),
    (r'CSIDL_CONTACTS', r'''On computers running Windows Vista, this refers to the Contacts folder in %CSIDL_PROFILE%.'''),
    (r'CSIDL_CONTROLS', r'''The virtual folder containing icons for the Control Panel applications.'''),
    (r'CSIDL_COOKIES', r'''The file system directory that serves as a common repository for Internet cookies. A typical path is C:\Documents and Settings\username\Cookies.'''),
    (r'CSIDL_DESKTOP', r'''The virtual folder representing the Windows desktop, the root of the namespace.'''),
    (r'CSIDL_DESKTOPDIRECTORY', r'''The file system directory used to physically store file objects on the desktop (which should not be confused with the desktop folder itself). A typical path is C:\Documents and Settings\username\Desktop.'''),
    (r'CSIDL_DRIVES', r'''The virtual folder representing My Computer, containing everything on the local computer: storage devices, printers, and Control Panel. The folder may also contain mapped network drives.'''),
    (r'CSIDL_FAVORITES', r'''The file system directory that serves as a common repository for the user's favorite items. A typical path is C:\Documents and Settings\username\Favorites.'''),
    (r'CSIDL_HISTORY', r'''The file system directory that serves as a common repository for Internet history items.'''),
    (r'CSIDL_INTERNET', r'''A virtual folder for Internet Explorer (icon on desktop).'''),
    (r'CSIDL_INTERNET_CACHE', r'''The file system directory that serves as a common repository for temporary Internet files. A typical path is C:\Documents and Settings\username\Local Settings\Temporary Internet Files.'''),
    (r'CSIDL_LOCAL_APPDATA', r'''The file system directory that serves as a data repository for local (nonroaming) applications. A typical path is C:\Documents and Settings\username\Local Settings\Application Data.'''),
    (r'CSIDL_MYDOCUMENTS', r'''The virtual folder representing the My Documents desktop item.'''),
    (r'CSIDL_MYMUSIC', r'''The file system directory that serves as a common repository for music files. A typical path is C:\Documents and Settings\User\My Documents\My Music.'''),
    (r'CSIDL_MYPICTURES', r'''The file system directory that serves as a common repository for image files. A typical path is C:\Documents and Settings\username\My Documents\My Pictures.'''),
    (r'CSIDL_MYVIDEO', r'''The file system directory that serves as a common repository for video files. A typical path is C:\Documents and Settings\username\My Documents\My Videos.'''),
    (r'CSIDL_NETHOOD', r'''A file system directory containing the link objects that may exist in the My Network Places virtual folder. It is not the same as CSIDL_NETWORK, which represents the network namespace root. A typical path is C:\Documents and Settings\username\NetHood.'''),
    (r'CSIDL_NETWORK', r'''A virtual folder representing My Network Places, the root of the network namespace hierarchy.'''),
    (r'CSIDL_PERSONAL', r'''**Version 6.0**: The virtual folder representing the My Documents desktop item. This is equivalent to CSIDL_MYDOCUMENTS.  **Previous to Version 6.0**: The file system directory used to physically store a user's common repository of documents. A typical path is C:\Documents and Settings\username\My Documents. This should be distinguished from the virtual My Documents folder in the namespace. To access that virtual folder, use SHGetFolderLocation, which returns the ITEMIDLIST for the virtual location, or refer to the technique described in Managing the File System (http://go.microsoft.com/fwlink/?LinkId=74611).'''),
    (r'CSIDL_PLAYLISTS', r'''For computers running Windows Vista, the virtual folder used to store play albums, typically username\My Music\Playlists.'''),
    (r'CSIDL_PRINTERS', r'''The virtual folder containing installed printers.'''),
    (r'CSIDL_PRINTHOOD', r'''The file system directory that contains the link objects that can exist in the Printers virtual folder. A typical path is C:\Documents and Settings\username\PrintHood.'''),
    (r'CSIDL_PROFILE', r'''The user's profile folder. A typical path is C:\Documents and Settings\username. Applications should not create files or folders at this level; they should put their data under the locations referred to by CSIDL_APPDATA or CSIDL_LOCAL_APPDATA.'''),
    (r'CSIDL_PROGRAMS', r'''The file system directory that contains the user's program groups (which are themselves file system directories). A typical path is C:\Documents and Settings\username\Start Menu\Programs.'''),
    (r'CSIDL_RECENT', r'''The file system directory that contains shortcuts to the user's most recently used documents. A typical path is C:\Documents and Settings\username\My Recent Documents. To create a shortcut in this folder, use SHAddToRecentDocs. In addition to creating the shortcut, this function updates the shell's list of recent documents and adds the shortcut to the My Recent Documents submenu of the Start menu.'''),
    (r'CSIDL_SENDTO', r'''The file system directory that contains Send To menu items. A typical path is C:\Documents and Settings\username\SendTo.'''),
    (r'CSIDL_STARTMENU', r'''The file system directory containing Start menu items. A typical path is C:\Documents and Settings\username\Start Menu.'''),
    (r'CSIDL_STARTUP', r'''The file system directory that corresponds to the user's Startup program group. A typical path is C:\Documents and Settings\username\Start Menu\Programs\Startup.'''),
    (r'CSIDL_TEMPLATES', r'''The file system directory that serves as a common repository for document templates. A typical path is C:\Documents and Settings\username\Templates.'''),
    (r'HOMEPATH', r'''Same as %USERPROFILE%.'''),
    (r'TEMP', r'''The temporary folder on the computer. For Windows XP, a typical path is %USERPROFILE%\Local Settings\Temp. For Windows Vista, a typical path is %USERPROFILE%\AppData\Local\Temp.'''),
    (r'TMP', r'''The temporary folder on the computer. For Windows XP, a typical path is %USERPROFILE%\Local Settings\Temp. For Windows Vista,, a typical path is %USERPROFILE%\AppData\Local\Temp.'''),
    (r'USERPROFILE', r'''Same as CSIDL_PROFILE.'''),
    (r'USERSID', r'''Represents the current user account security identifier (SID). For example, `S-1-5-21-1714567821-1326601894-715345443-1026.`''')])

SYSTEM_DIRECTORIES = resolve_csidl_paths(CSIDL_SYSTEM_DESCRIPTIONS)
USER_DIRECTORIES = resolve_csidl_paths(CSIDL_USER_DESCRIPTIONS)


def local_app_data():
    return USER_DIRECTORIES['LOCAL_APPDATA']


def my_documents():
    return USER_DIRECTORIES['PERSONAL']


def common_app_data():
    return SYSTEM_DIRECTORIES['COMMON_APPDATA']


__all__ = [CSIDL_SYSTEM_DESCRIPTIONS, CSIDL_USER_DESCRIPTIONS,
           SYSTEM_DIRECTORIES, USER_DIRECTORIES, local_app_data, my_documents,
           common_app_data]
