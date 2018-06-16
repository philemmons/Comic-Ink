-- phpMyAdmin SQL Dump
-- version 4.0.10deb1
-- http://www.phpmyadmin.net
--
-- Host: 127.0.0.1
-- Generation Time: May 08, 2017 at 04:04 AM
-- Server version: 5.5.54-0ubuntu0.14.04.1
-- PHP Version: 5.5.9-1ubuntu4.21

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8 */;

--
-- Database: `comicDB`
--

-- --------------------------------------------------------

--
-- Table structure for table `convention`
--

CREATE TABLE IF NOT EXISTS `convention` (
  `con_id` int(11) NOT NULL AUTO_INCREMENT,
  `conName` varchar(60) NOT NULL,
  `city` varchar(25) NOT NULL,
  `state` varchar(10) NOT NULL,
  `creator` varchar(40),
  `website` varchar(40),
  `turnOut` int(11),
  PRIMARY KEY (`con_id`)
) ENGINE=InnoDB  DEFAULT CHARSET=latin1 AUTO_INCREMENT=18 ;

--
-- Dumping data for table `convention`
--

INSERT INTO `convention` (`con_id`, `conName`, `city`, `state`, `creator`, `website`, `turnOut`) VALUES
(1, 'silicon valley comic con', 'san jose', 'CA', 'stan lee', 'http://svcomiccon.com', 60000),
(2, 'san diego comic-con international', 'san diego', 'CA', 'sergio aragones', 'https://www.comic-con.org/', 167000),
(3, 'new york comic con', 'new york', 'NY', 'dave gibbons', 'http://www.newyorkcomiccon.com', 151000),
(4, 'comikaze expo', 'los angeles', 'CA', 'neal adams', 'http://www.stanleeslacomiccon.com', 65000),
(5, 'emerald city comic con', 'seattle', 'WA', 'frank miller', 'http://www.emeraldcitycomicon.com', 88000),
(6, 'phoenix comicon', 'phoenix', 'AR', 'scott mccloud', 'https://phoenixcomicon.com/', 106000),
(7, 'dragon con', 'atlanta', 'GA', 'jim starlin', 'http://www.dragoncon.org', 77000),
(8, 'motor city comic con', 'novi', 'MI', 'frank cho', 'http://motorcitycomiccon.com', 50000),
(10, 'megacon', 'orlando', 'FL', 'bill sienkiewicz', 'http://megaconorlando.com/', 101000);

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
