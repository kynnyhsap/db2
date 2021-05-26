<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns="http://www.w3.org/1999/xhtml">
    <xsl:output
        method="xml"
        doctype-system="http://www.w3.org/TR/xhtml11/DTD/xhtml11.dtd"
        doctype-public="-//W3C//DTD XHTML 1.1//EN"
        indent="yes"
    />
    <xsl:template match="/">
        <html xml:lang="en">
            <head>
                <title>Lab 1 Task 4</title>
            </head>
            <body>
                <h1>Products:</h1>
                <xsl:apply-templates select="/root"/>
                <xsl:if test="count(/root/product) = 0">
                    <p>No products</p>
                </xsl:if>
            </body>
        </html>
    </xsl:template>
    <xsl:template match="/root">
        <table border="1">
            <thead>
                <tr>
                    <td>image</td>
                    <td>description</td>
                    <td>price</td>
                </tr>
            </thead>
            <tbody>
                <xsl:apply-templates select="/root/product"/>
            </tbody>
        </table>
    </xsl:template>
    <xsl:template match="/root/product">
        <tr>
            <td>
                 <xsl:apply-templates select="image"/>
            </td>
            <td>
                <xsl:apply-templates select="description"/>
            </td>
            <td>
                <xsl:apply-templates select="price"/>
            </td>
        </tr>
    </xsl:template>
    <xsl:template match="image">
        <img alt="image of product">
            <xsl:attribute name="src">
                <xsl:value-of select="text()"/>
            </xsl:attribute>
        </img>
    </xsl:template>
    <xsl:template match="price">
        <xsl:value-of select="text()"/>
    </xsl:template>
    <xsl:template match="description">
        <xsl:value-of select="text()"/>
    </xsl:template>
</xsl:stylesheet>